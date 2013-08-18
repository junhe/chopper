cmake_minimum_required (VERSION 2.6)


project (Metawalker)

set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wall") 
set(CMAKE_C_FLAGS  "${CMAKE_C_FLAGS} -Wall") 
set(CMAKE_CXX_COMPILER "mpicxx")
#set(CMAKE_VERBOSE_MAKEFILE true)

add_definitions("-D_FILE_OFFSET_BITS=64")

add_subdirectory (src)

