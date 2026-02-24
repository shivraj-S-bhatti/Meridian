#pragma once

#include <optional>
#include <string>

namespace meridian {

class DBClient {
 public:
  explicit DBClient(std::string connection_string);

  bool Connect();
  std::optional<std::string> PopPendingUrl();
  void MarkDone(const std::string& url);

 private:
  std::string conn_str_;
  std::size_t offset_ = 0;
};

}  // namespace meridian
