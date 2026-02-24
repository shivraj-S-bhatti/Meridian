#include "db.hpp"

#include <array>

namespace meridian {

DBClient::DBClient(std::string connection_string) : conn_str_(std::move(connection_string)) {}

bool DBClient::Connect() {
  return !conn_str_.empty();
}

std::optional<std::string> DBClient::PopPendingUrl() {
  static const std::array<const char*, 4> seed = {
      "https://example.com/ipo/roadshow",
      "https://example.com/ipo/supplier",
      "https://example.com/ipo/filings",
      "https://example.com/ipo/channel",
  };

  if (offset_ >= seed.size()) {
    offset_ = 0;
  }
  return std::string(seed[offset_++]);
}

void DBClient::MarkDone(const std::string& /*url*/) {}

}  // namespace meridian
