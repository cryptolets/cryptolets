#include "tb_helper.h"

/*
A run_per_row would look like this; e.g. for adder:

vector<string> run_per_row(vector<string>& samples_row) {
  ac_int<N, false> x = parse_ac_int<N>(samples_row[0]);
  ac_int<N, false> y = parse_ac_int<N>(samples_row[1]);
  ac_int<N+1, false> result = CCS_DESIGN(add_f)(x, y);
  return {to_string(x), to_string(y), to_string(result)};
}
*/

// A generic testbench runner 
void run_tb(
  vector<string> (*run_per_row)(vector<string>& samples_row),
  string samples_file,
  string output_file
) {
  // define data structure for holding input and output samples:
  csv_t samples;
  csv_t samples_out;

  // read in samples from CSV file
  if (ReadCSV_Samples(samples_file, samples) < 0) {
    cerr << __FILE__ << ":" << __LINE__ << " - Failed to read input samples" << endl;
    return;
  }

  // Loop through samples, applying them to the function
  for (auto &samples_row : samples) {
    samples_out.push_back(run_per_row(samples_row));
  }

  WriteCSV_Samples(output_file, samples_out);

  cout << __FILE__ << ":" << __LINE__ << " - End of testbench." << endl;
}


// Reads testbench sample data from a CSV file formatted as
//   i0,i1,i2, ...
// Values are returned in the vector passed by reference.
// Returns -1 on error, else returns the number of samples read in.
int ReadCSV_Samples(string filename, csv_t &samples)
{
  CsvParser  *csvparser = CsvParser_new(filename.c_str(), ",", 1);
  CsvRow   *row;
  const CsvRow *header = CsvParser_getHeader(csvparser);

  if (header == NULL) {
    cerr << CsvParser_getErrorMessage(csvparser) << endl;
    return -1;
  }

  int n = CsvParser_getNumFields(header);
  while ((row = CsvParser_getRow(csvparser)) ) {
    const char **rowFields = CsvParser_getFields(row);
    vector<string> parsed_row;
    for (int i = 0; i < n; i++) parsed_row.push_back(rowFields[i]);
    samples.push_back(parsed_row);
    CsvParser_destroy_row(row);
  }
  cout << __FILE__ << ":" << __LINE__ << " - CSV file '" << filename << "' " << samples.size() << " samples were read in." << endl;
  CsvParser_destroy(csvparser);
  return samples.size();
}


// Writes testbench output sample data to a CSV file formatted as o0,o1,o2, ...
bool WriteCSV_Samples(string oFileName, csv_t &samples)
{
    // create output csv file with results:
    ofstream oSampleFile;
    cout << __FILE__ << ":" << __LINE__ << " - Writing output csv file to '" << oFileName << "'." << endl;
    oSampleFile.open(oFileName.c_str());
    if (!oSampleFile.is_open()) {
        cerr << __FILE__ << ":" << __LINE__ << " - CSV output file '" << oFileName << "' could not be created." << endl;
        return false;
    }

    if (samples.empty()) { oSampleFile.close(); return true; }
    for (int i = 0; i < samples[0].size()-1; i++) 
        oSampleFile << "o" << i << ",";
    oSampleFile << "o" << samples[0].size()-1 << endl;

    for (auto &samples_row : samples) {
        for (size_t i = 0; i < samples_row.size() - 1; i++) 
            oSampleFile << samples_row[i] << ",";
        oSampleFile << samples_row.back() << endl;
    }
    oSampleFile.close();
    return true;
}