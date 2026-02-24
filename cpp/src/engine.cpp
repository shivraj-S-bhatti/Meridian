#include "engine.hpp"

#include <chrono>
#include <iostream>

namespace meridian {

Engine::Engine(std::string db_conn, int workers)
    : db_(std::move(db_conn)), workers_(workers), running_(false) {}

Engine::~Engine() {
  Stop();
}

void Engine::Start() {
  if (running_.exchange(true)) {
    return;
  }

  db_.Connect();
  for (int i = 0; i < workers_; ++i) {
    threads_.emplace_back(&Engine::WorkerLoop, this, i);
  }
}

void Engine::Stop() {
  if (!running_.exchange(false)) {
    return;
  }

  for (auto& t : threads_) {
    if (t.joinable()) {
      t.join();
    }
  }
  threads_.clear();
}

void Engine::WorkerLoop(int id) {
  while (running_) {
    const auto maybe_url = db_.PopPendingUrl();
    if (!maybe_url.has_value()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
      continue;
    }

    const auto body = fetcher_.Fetch(*maybe_url);
    std::cout << "worker=" << id << " url=" << *maybe_url << " bytes=" << body.size() << "\n";
    db_.MarkDone(*maybe_url);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
}

}  // namespace meridian
