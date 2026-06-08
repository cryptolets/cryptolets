#include "point_double.h"

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
  EC_point_J P0;
  wide_t q_sample;
  wide_t q_prime_sample;
  wide_2x_t mu_sample;
  wide_t field_a_sample;
  EC_point_J o_sample;
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

//=============================================================================
// Function: main
//   Test the point_double() function using data from CSV files
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

  // Loop through samples, applying them to the function
  for (vector<STIMULUS_TYPE>::iterator it = samples.begin(); it != samples.end(); ++it) {
    STIMULUS_TYPE stimulus_element = *it;

    stimulus_element.o_sample = CCS_DESIGN(point_double)(
      stimulus_element.P0

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

#if (CURVE_PARAMS_TYPE == VAR_CURVE_PARAMS) && (FIELD_A == AVAR)
    , stimulus_element.field_a_sample
#endif
    );

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

  const char **headerFields = CsvParser_getFields(header);
  while ((row = CsvParser_getRow(csvparser)) ) {
    const char **rowFields = CsvParser_getFields(row);
    STIMULUS_TYPE stimulus_element;
    stimulus_element.P0.X = parse_ac_int<wide_t::width>(rowFields[0]);
    stimulus_element.P0.Y = parse_ac_int<wide_t::width>(rowFields[1]);
    stimulus_element.P0.Z = parse_ac_int<wide_t::width>(rowFields[2]);
    
    stimulus_element.q_sample = parse_ac_int<wide_t::width>(rowFields[3]);

  #if MODMUL_TYPE == MODMUL_TYPE_BARRETT
    stimulus_element.mu_sample = parse_ac_int<wide_2x_t::width>(rowFields[4]);
  #else
    stimulus_element.q_prime_sample = parse_ac_int<wide_t::width>(rowFields[4]);
  #endif

    stimulus_element.field_a_sample = parse_ac_int<wide_t::width>(rowFields[5]);

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
  oSampleFile << "X3,Y3,Z3" << endl;
  for (samplesVector_t::iterator it = samples.begin(); it != samples.end(); ++it) {
    oSampleFile << (*it).o_sample.X << "," << (*it).o_sample.Y <<  "," << (*it).o_sample.Z << endl;
  }
  oSampleFile.close();
  return true;
}
