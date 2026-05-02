#ifndef TB_HELPER_H
#define TB_HELPER_H

#include <iostream>
#include <vector>
#include <assert.h>
#include <fstream>
#include <mc_scverify.h>
#include <string>
#include <ac_int.h>
using namespace std;

typedef vector<vector<string>> csv_t;
const string SAMPLES_FILE = "samples/samples.csv";
const string OUTPUT_FILE  = "outputs/output.csv";

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

void run_tb(vector<string> (*run_per_row)(vector<string>& samples_row));
int ReadCSV_Samples(string filename, csv_t &samples);
bool WriteCSV_Samples(string oFileName, csv_t &samples);

#endif // TB_HELPER_H