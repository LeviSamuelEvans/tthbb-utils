//                                                          //
// Basic script to check event yields in L2 samples LE v0.2 //
//                                                          //

// - Requires user input of directory containing .root files 
// - compile using g++ -o EventYeilds EventYeilds.cpp `root-config --cflags --libs`
// - This will create an executable that can be run with ./EventYeilds

#include <iostream>
#include <fstream>
#include <string>
#include <dirent.h>
#include "TFile.h"
#include "TTree.h"

void getEntries(const char* filename) {
    // Open each root file 
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
    Long64_t nSelected = tree->GetEntries("");
    std::cout << "Selected entries: " << nSelected << std::endl;
    // Clean up
    file->Close();
    delete file;
}

int main() {
    // Prompt user to enter directory path
    std::cout << "Enter directory path: ";
    std::string dir_path;
    std::getline(std::cin, dir_path);
    // Open directory and loop over all .root files in it
    DIR* dir = opendir(dir_path.c_str());
    if (!dir) {
        std::cerr << "Error: could not open directory " << dir_path << std::endl;
        return 1;
    }
    dirent* entry;
    while ((entry = readdir(dir))) {
        std::string filename = entry->d_name;
        if (filename.rfind(".root") == filename.length() - 5) {
            std::string full_path = dir_path + "/" + filename;
            getEntries(full_path.c_str());
        }
    }
    // Clean up
    closedir(dir);
    return 0;
}

