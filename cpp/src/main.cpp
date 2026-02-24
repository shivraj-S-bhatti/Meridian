#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>

#include "engine.hpp"

int main(int argc, char** argv) {
  std::string db = "postgresql://crawler:crawler@localhost:5432/crawler";
  int workers = 8;

  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--db" && i + 1 < argc) {
      db = argv[++i];
    } else if (arg == "--workers" && i + 1 < argc) {
      workers = std::max(1, std::atoi(argv[++i]));
    }
  }

  std::cout << "starting stashy_engine db=" << db << " workers=" << workers << "\n";
  meridian::Engine engine(db, workers);
  engine.Start();

  std::this_thread::sleep_for(std::chrono::seconds(2));
  engine.Stop();
  std::cout << "engine stopped\n";
  return 0;
}
