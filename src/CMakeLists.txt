include_directories ( ${Metawalker_SOURCE_DIR}/src )
link_directories (${Metawalker_SOURCE_DIR}/src)

add_library (Util Util.cpp)
add_library (WorkloadFetcher WorkloadFetcher.cpp)


add_executable(player player.cpp)
target_link_libraries(player Util WorkloadFetcher)

