
//                                                          //
// Basic script to check event yields in L2 samples LE v0.1 //
//                                                          //

// - Requires a .txt file containting all root files to run over and print outputs to terminal/ log files 
// - compile using g++ -o EventYeilds EventYeilds.cpp `root-config --cflags --libs`


#include <iostream>
#include <fstream>
#include <string>
#include "TFile.h"
#include "TTree.h"

void getEntries(const char* filename) {
    // Open root file
    TFile* file = new TFile(filename, "READ");
    if (!file || file->IsZombie()) {
        std::cerr << "Error: could not open file " << filename << std::endl;
        return;
    }
    // Get nominal tree inside the .root file (i.e "nominal_Loose")
    TTree* tree = (TTree*)file->Get("nominal_Loose");
    if (!tree) {
        std::cerr << "Error: could not find tree 'nominal_Loose' in file " << filename << std::endl;
        file->Close();
        return;
    }
    // Get entries for each sample
    Long64_t nEntries = tree->GetEntries();
    std::cout << "File: " << filename << std::endl;
    std::cout << "Entries: " << nEntries << std::endl;
    // Get entry yields, can add cuts here as you please ( i.e for regions used in fit setup/ inclusive phase space)
    Long64_t nSelected = tree->GetEntries("your_cut_here");
    std::cout << "Selected entries: " << nSelected << std::endl;
    // Clean up
    file->Close();
    delete file;
}

int main() {
    // Open file with list of file names using a .txt file
    std::ifstream infile("file_list.txt");
    if (!infile) {
        std::cerr << "Error: could not open file_list.txt" << std::endl;
        return 1;
    }
    // Loop over file names and print GetEntries values to terminal/log files 
    std::string filename;
    while (std::getline(infile, filename)) {
        getEntries(filename.c_str());
    }
    // Clean up
    infile.close();
    return 0;
}
