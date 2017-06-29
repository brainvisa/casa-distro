
set( _headers
  custom_project.h
)

set( _sources
  custom_project.cc
)


BRAINVISA_COPY_AND_INSTALL_HEADERS( _headers custom_project headersTarget )
add_library( custom_project SHARED ${_sources} )
add_dependencies( custom_project ${headersTarget} )
set_property( TARGET custom_project PROPERTY VERSION ${${PROJECT_NAME}_VERSION} )
# target_link_libraries( custom_project graph cartodata )
BRAINVISA_INSTALL( TARGETS custom_project
                    DESTINATION lib
                    COMPONENT ${PROJECT_NAME} )

BRAINVISA_ADD_EXECUTABLE(test_custom_project
    test_custom_project.cc
)

TARGET_LINK_LIBRARIES(test_custom_project
    custom_project
)

# BRAINVISA_ADD_SIP_PYTHON_MODULE( custom_project_sip 
#   custom_project
#   "${_mainSipFile}" 
#   SIP_SOURCES custom_project.sip
#   SIP_INCLUDE  "${CMAKE_BINARY_DIR}/${AIMS_RELATIVE_SIP_DIRECTORY}"
#   SIP_INSTALL "${AIMS_RELATIVE_SIP_DIRECTORY}")
# target_link_libraries( custom_project_sip "${PYTHON_LIBRARY}")
# add_dependencies( custom_project_sip ${headersTarget} )
# BRAINVISA_INSTALL( TARGETS custom_project_sip 
#                    DESTINATION python/custom_project
#                    COMPONENT ${PROJECT_NAME} )

