#include "ntt.h"

// Include utility headers
#include <iostream>
#include "csvparser.h"
#include <vector>
#include <assert.h>
#include <string>
#include <sstream>
#include <fstream>
#include <mc_scverify.h>
using namespace std;

// Define types used by this program
struct STIMULUS_TYPE {
  wide_t a_sample[NTT_LEN];
  wide_t omega_sample[NTT_LEN/2];
  wide_t inverse_omega_sample[NTT_LEN/2];
  wide_t n_inv_sample;
  wide_t q_sample;
  wide_t q_prime_sample;
  wide_2x_t mu_sample;
  wide_t ntt_o_sample[NTT_LEN];
  wide_t intt_o_sample[NTT_LEN];
};

typedef vector<STIMULUS_TYPE> samplesVector_t;

// Forward Declarations of utility functions
int  ReadCSV_Samples(string filename, samplesVector_t &samples);
bool WriteCSV_Samples(string, samplesVector_t &samples);

// helper
template<int W>
ac_int<W, false> parse_ac_int(const std::string &str) {
    ac_int<W, false> v = 0;
    for (char c : str) {
        if (c < '0' || c > '9') break; // stop at first non-digit
        v *= 10;
        v += (c - '0');
    }
    return v;
}

void copy_input_vector(
    wide_t in[NTT_LEN],
    wide_t out[NTT_LEN])
{
  COPY_INPUT_VECTOR: for (int i = 0; i < NTT_LEN; i++) {
    out[i] = in[i];
  }
}

void clear_vector(
    wide_t out[NTT_LEN])
{
  CLEAR_VECTOR: for (int i = 0; i < NTT_LEN; i++) {
    out[i] = 0;
  }
}

void copy_active_result(
    wide_t ping[NTT_LEN],
    wide_t pong[NTT_LEN],
    wide_t out[NTT_LEN])
{
  if ((NUM_STAGES % 2) == 0) {
    COPY_PING_RESULT: for (int i = 0; i < NTT_LEN; i++) {
      out[i] = ping[i];
    }
  } else {
    COPY_PONG_RESULT: for (int i = 0; i < NTT_LEN; i++) {
      out[i] = pong[i];
    }
  }
}

//=============================================================================
// Function: main
//   Test the ntt() and intt() functions using data from CSV files
//-----------------------------------------------------------------------------
CCS_MAIN(int argc, char **argv)    // required for sc verify flow in Catapult
{
  // Process options
  string samples_file = "samples/samples_" + to_string(BITWIDTH) + ".csv";
  string output_file  = "outputs/output_"  + to_string(BITWIDTH) + ".csv";

  if (argc == 3) {
    samples_file = argv[1];
    output_file = argv[2];
  }

  // define data structure for holding input and output samples:
  samplesVector_t samples;
  samplesVector_t samples_out;

  // read in samples from CSV file
  if (ReadCSV_Samples(samples_file.c_str(), samples) < 0) {
    cerr << __FILE__ << ":" << __LINE__ << " - Failed to read input samples" << endl;
    return -1;
  }

  // Loop through samples, applying them to the functions
  for (vector<STIMULUS_TYPE>::iterator it = samples.begin(); it != samples.end(); ++it) {
    STIMULUS_TYPE stimulus_element = *it;

    wide_t ntt_ping[NTT_LEN];
    wide_t ntt_pong[NTT_LEN];
    wide_t intt_ping[NTT_LEN];
    wide_t intt_pong[NTT_LEN];

    copy_input_vector(stimulus_element.a_sample, ntt_ping);
    copy_input_vector(stimulus_element.a_sample, intt_ping);
    clear_vector(ntt_pong);
    clear_vector(intt_pong);

    CCS_DESIGN(ntt)(
      stimulus_element.omega_sample,
      ntt_ping,
      ntt_pong

#if Q_TYPE == VAR_Q
    , stimulus_element.q_sample
#endif

#if REDC_TYPE == VAR_RC
    #if MODMUL_TYPE == MODMUL_TYPE_MONT
        , stimulus_element.q_prime_sample
    #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        , stimulus_element.mu_sample
    #endif
#endif
    );

    CCS_DESIGN(intt)(
      stimulus_element.inverse_omega_sample,
      intt_ping,
      intt_pong,
      stimulus_element.n_inv_sample

#if Q_TYPE == VAR_Q
    , stimulus_element.q_sample
#endif

#if REDC_TYPE == VAR_RC
    #if MODMUL_TYPE == MODMUL_TYPE_MONT
        , stimulus_element.q_prime_sample
    #elif MODMUL_TYPE == MODMUL_TYPE_BARRETT
        , stimulus_element.mu_sample
    #endif
#endif
    );

    copy_active_result(ntt_ping, ntt_pong, stimulus_element.ntt_o_sample);
    copy_active_result(intt_ping, intt_pong, stimulus_element.intt_o_sample);

    samples_out.push_back(stimulus_element);
  }

  WriteCSV_Samples(output_file.c_str(), samples_out);

  cout << __FILE__ << ":" << __LINE__ << " - End of testbench." << endl;
  CCS_RETURN(0);
}

int ReadCSV_Samples(string filename, samplesVector_t &samples)
{
  CsvParser  *csvparser = CsvParser_new(filename.c_str(), ",", 1);
  CsvRow   *row;
  const CsvRow *header = CsvParser_getHeader(csvparser);

  if (header == NULL) {
    cerr << CsvParser_getErrorMessage(csvparser) << endl;
    return -1;
  }

  assert(CsvParser_getNumFields(header) == (2 * NTT_LEN + 3));

  const char **headerFields = CsvParser_getFields(header);
  while ((row = CsvParser_getRow(csvparser)) ) {
    const char **rowFields = CsvParser_getFields(row);
    STIMULUS_TYPE stimulus_element;

    int col_idx = 0;

    READ_INPUT: for (int i = 0; i < NTT_LEN; i++) {
      stimulus_element.a_sample[i] = parse_ac_int<wide_t::width>(rowFields[col_idx]);
      col_idx++;
    }

    READ_OMEGAS: for (int i = 0; i < NTT_LEN/2; i++) {
      stimulus_element.omega_sample[i] = parse_ac_int<wide_t::width>(rowFields[col_idx]);
      col_idx++;
    }

    READ_INVERSE_OMEGAS: for (int i = 0; i < NTT_LEN/2; i++) {
      stimulus_element.inverse_omega_sample[i] = parse_ac_int<wide_t::width>(rowFields[col_idx]);
      col_idx++;
    }

    stimulus_element.n_inv_sample = parse_ac_int<wide_t::width>(rowFields[col_idx]);
    col_idx++;

    stimulus_element.q_sample = parse_ac_int<wide_t::width>(rowFields[col_idx]);
    col_idx++;

  #if MODMUL_TYPE == MODMUL_TYPE_BARRETT
    stimulus_element.mu_sample = parse_ac_int<wide_2x_t::width>(rowFields[col_idx]);
  #else
    stimulus_element.q_prime_sample = parse_ac_int<wide_t::width>(rowFields[col_idx]);
  #endif

    samples.push_back(stimulus_element);
    CsvParser_destroy_row(row);
  }
  cout << __FILE__ << ":" << __LINE__ << " - CSV file '" << filename << "' " << samples.size() << " samples were read in." << endl;
  CsvParser_destroy(csvparser);
  return samples.size();
}


bool WriteCSV_Samples(string oFileName, samplesVector_t &samples)
{
  // create output csv file with results:
  ofstream oSampleFile;
  cout << __FILE__ << ":" << __LINE__ << " - Writing output csv file to '" << oFileName << "'." << endl;
  oSampleFile.open(oFileName.c_str());
  if (!oSampleFile.is_open()) {
    cerr << __FILE__ << ":" << __LINE__ << " - CSV output file '" << oFileName << "' could not be created." << endl;
    return false;
  }

  for (int i = 0; i < NTT_LEN; i++) {
    if (i != 0) {
      oSampleFile << ",";
    }
    oSampleFile << "ntt_o" << i << "_sample";
  }

  WRITE_INTT_HEADER: for (int i = 0; i < NTT_LEN; i++) {
    oSampleFile << "," << "intt_o" << i << "_sample";
  }
  oSampleFile << endl;

  for (samplesVector_t::iterator it = samples.begin(); it != samples.end(); ++it) {
    WRITE_NTT_OUTPUT: for (int i = 0; i < NTT_LEN; i++) {
      if (i != 0) {
        oSampleFile << ",";
      }
      oSampleFile << (*it).ntt_o_sample[i];
    }

    WRITE_INTT_OUTPUT: for (int i = 0; i < NTT_LEN; i++) {
      oSampleFile << "," << (*it).intt_o_sample[i];
    }
    oSampleFile << endl;
  }
  oSampleFile.close();
  return true;
}
