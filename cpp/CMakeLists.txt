cmake_minimum_required(VERSION 3.16)
project(stashy_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(CURL)
find_package(PkgConfig)
if(PkgConfig_FOUND)
  pkg_check_modules(PQ libpq)
endif()

add_executable(stashy_engine
  src/main.cpp
  src/engine.cpp
  src/fetcher.cpp
  src/db.cpp
)

target_include_directories(stashy_engine PRIVATE src)

if(CURL_FOUND)
  target_compile_definitions(stashy_engine PRIVATE HAS_CURL=1)
  target_include_directories(stashy_engine PRIVATE ${CURL_INCLUDE_DIRS})
  target_link_libraries(stashy_engine PRIVATE ${CURL_LIBRARIES})
endif()

if(PQ_FOUND)
  target_compile_definitions(stashy_engine PRIVATE HAS_LIBPQ=1)
  target_include_directories(stashy_engine PRIVATE ${PQ_INCLUDE_DIRS})
  target_link_libraries(stashy_engine PRIVATE ${PQ_LIBRARIES})
endif()
