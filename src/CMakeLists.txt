include_directories ( ${Metawalker_SOURCE_DIR}/src )
link_directories (${Metawalker_SOURCE_DIR}/src)

add_library (Util Util.cpp)
add_library (Logger Logger.cpp)
add_library (WorkloadFetcher WorkloadFetcher.cpp)
add_library (WorkloadPlayer WorkloadPlayer.cpp)


add_executable(player player.cpp)
add_executable(puncher puncher.cpp)
add_executable(filefiller filefiller.cpp)
target_link_libraries(player  WorkloadFetcher Util WorkloadPlayer)
target_link_libraries(puncher Logger)
target_link_libraries(filefiller Logger)

