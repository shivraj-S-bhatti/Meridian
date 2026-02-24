#pragma once

#include <string>

namespace meridian {

class Fetcher {
 public:
  std::string Fetch(const std::string& url) const;
};

}  // namespace meridian
