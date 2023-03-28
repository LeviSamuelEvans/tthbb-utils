/* Script to check event yields in L2 samples LE v0.3

 - compile using g++ -o EventYields_v0.3 EventYields_v0.3.cpp `root-config --cflags --libs`
 - This will create an executable that can be run with ./EventYeilds

*/

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <dirent.h>
#include <sys/stat.h>
#include <iomanip>
#include "TFile.h"
#include "TTree.h"

std::ofstream logFile;

void printProgressBar(int progress, int total) {
    const int barWidth = 50;
    float percentage = static_cast<float>(progress) / static_cast<float>(total);

    std::cout << "[";
    int pos = barWidth * percentage;
    for (int i = 0; i < barWidth; ++i) {
        if (i < pos) std::cout << "=";
        else if (i == pos) std::cout << ">";
        else std::cout << " ";
    }
    std::cout << "] " << int(percentage * 100.0) << " %\r";
    std::cout.flush();
}

int countRootFiles(const std::string& dir_path) {
    DIR* dir = opendir(dir_path.c_str());
    if (!dir) {
        return 0;
    }
    int count = 0;
    dirent* entry;
    while ((entry = readdir(dir))) {
        std::string filename = entry->d_name;
        std::string full_path = dir_path + "/" + filename;
        struct stat buf;
        stat(full_path.c_str(), &buf);
        if (S_ISDIR(buf.st_mode)) {
            if (filename != "." && filename != "..") {
                count += countRootFiles(full_path);
            }
        } else if (filename.rfind(".root") == filename.length() - 5) {
            count++;
        }
    }
    closedir(dir);
    return count;
}

void getEntries(const std::string& sampleName, const char* filename, int& progress, int total) {
    TFile* file = new TFile(filename, "READ");
    if (!file || file->IsZombie()) {
        logFile << "Error: could not open file " << filename << std::endl;
        return;
    }
    TTree* tree = (TTree*)file->Get("nominal_Loose");
    if (!tree) {
        logFile << "Error: could not find tree 'nominal_Loose' in file " << filename << std::endl;
        file->Close();
        return;
    }
    Long64_t nEntries = tree->GetEntries();
    Long64_t nSelected = tree->GetEntries("");
    logFile << std::left << std::setw(40) << sampleName << std::setw(20) << nEntries << std::setw(20) << nSelected << std::endl;
    file->Close();
    delete file;

    progress++;
    printProgressBar(progress, total);
}

void processDirectory(const std::string& dir_path) {
    int progress = 0;
    int total = countRootFiles(dir_path);
    DIR* dir = opendir(dir_path.c_str());
    if (!dir) {
        logFile << "Error: could not open directory " << dir_path << std::endl;
        return;
    }
    dirent* entry;
    while ((entry = readdir(dir))) {
        std::string filename = entry->d_name;
        std::string full_path = dir_path + "/" + filename;
        struct stat buf;
        stat(full_path.c_str(), &buf);
        if (S_ISDIR(buf.st_mode)) {
            if (filename != "." && filename != "..") {
                logFile << "\nDirectory: " << full_path << std::endl;
                logFile << std::left << std::setw(40) << "Sample" << std::setw(20) << "Entries" << std::setw(20) << "Selected Entries" << std::endl;
                logFile << std::string(80, '-') << std::endl;
                processDirectory(full_path);
            }
        } else if (filename.rfind(".root") == filename.length() - 5) {
            std::string sampleName = filename.substr(0, filename.length() - 5);
            getEntries(sampleName, full_path.c_str(), progress, total);
        }
    }
    closedir(dir);
}

int main() {
    std::cout << "Enter directory path: ";
    std::string dir_path;
    std::getline(std::cin, dir_path);
    std::string logFilePath = "EventYields_2l.log";
    logFile.open(logFilePath);
    if (!logFile) {
        std::cerr << "Error: could not open log file " << logFilePath << std::endl;
        return 1;
    }
    processDirectory(dir_path);
    logFile.close();
    std::cout << "Results saved to " << logFilePath << std::endl;
    return 0;
}
