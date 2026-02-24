#pragma once

#include <atomic>
#include <string>
#include <thread>
#include <vector>

#include "db.hpp"
#include "fetcher.hpp"

namespace meridian {

class Engine {
 public:
  Engine(std::string db_conn, int workers);
  ~Engine();

  void Start();
  void Stop();

 private:
  void WorkerLoop(int id);

  DBClient db_;
  Fetcher fetcher_;
  int workers_;
  std::atomic<bool> running_;
  std::vector<std::thread> threads_;
};

}  // namespace meridian
