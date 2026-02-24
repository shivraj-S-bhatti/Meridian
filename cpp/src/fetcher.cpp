#include "fetcher.hpp"

#include <sstream>

#ifdef HAS_CURL
#include <curl/curl.h>
#endif

namespace meridian {

#ifdef HAS_CURL
namespace {
size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
  const size_t total = size * nmemb;
  static_cast<std::string*>(userp)->append(static_cast<char*>(contents), total);
  return total;
}
}  // namespace
#endif

std::string Fetcher::Fetch(const std::string& url) const {
#ifdef HAS_CURL
  CURL* curl = curl_easy_init();
  if (!curl) {
    return "";
  }
  std::string buffer;
  curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
  curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
  curl_easy_perform(curl);
  curl_easy_cleanup(curl);
  return buffer;
#else
  std::ostringstream ss;
  ss << "<html><body><p>stub fetch for " << url << "</p></body></html>";
  return ss.str();
#endif
}

}  // namespace meridian
