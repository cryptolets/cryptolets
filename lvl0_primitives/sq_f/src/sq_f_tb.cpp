#include "sq_f.h"

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
  wide_t a_sample;
  wide_2x_t o_sample;
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
//   Test the sq_f() function using data from CSV files
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

    stimulus_element.o_sample = CCS_DESIGN(sq_f)(
      stimulus_element.a_sample
    );

    samples_out.push_back(stimulus_element);
  }

  WriteCSV_Samples(output_file.c_str(), samples_out);

  cout << __FILE__ << ":" << __LINE__ << " - End of testbench." << endl;
  CCS_RETURN(0);
}

//=============================================================================
// Function: ReadCSV_Samples
//   Reads testbench sample data from a CSV file formatted as
//     a_sample
//   Values are returned in the vector passed by reference.
//   Returns -1 on error, else returns the number of samples read in.
//-----------------------------------------------------------------------------
int ReadCSV_Samples(string filename, samplesVector_t &samples)
{
  CsvParser  *csvparser = CsvParser_new(filename.c_str(), ",", 1);
  CsvRow   *row;
  const CsvRow *header = CsvParser_getHeader(csvparser);

  if (header == NULL) {
    cerr << CsvParser_getErrorMessage(csvparser) << endl;
    return -1;
  }
  // CSV file is expected to have 1 columns: a_sample
  assert(CsvParser_getNumFields(header)==1);

  const char **headerFields = CsvParser_getFields(header);
  while ((row = CsvParser_getRow(csvparser)) ) {
    const char **rowFields = CsvParser_getFields(row);
    STIMULUS_TYPE stimulus_element;
    stimulus_element.a_sample = parse_ac_int<wide_t::width>(rowFields[0]);
    samples.push_back(stimulus_element);
    CsvParser_destroy_row(row);
  }
  cout << __FILE__ << ":" << __LINE__ << " - CSV file '" << filename << "' " << samples.size() << " samples were read in." << endl;
  CsvParser_destroy(csvparser);
  return samples.size();
}


// Function: WriteCSV_Samples
//   Writes testbench output sample data to a CSV file formatted as
//     o_sample
//
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
  oSampleFile << "o_sample" << endl;
  for (samplesVector_t::iterator it = samples.begin(); it != samples.end(); ++it) {
    oSampleFile << (*it).o_sample << endl;
  }
  oSampleFile.close();
  return true;
}