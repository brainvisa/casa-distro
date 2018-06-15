#! /bin/sh

# This script builds dcmtk
__download=1
__install=1
__install_prefix=/usr/local
__build_proc_num=4
__tmp_dir=/tmp
__download_dir=${__tmp_dir}
__build_dir=${__tmp_dir}

pushd ${__tmp_dir}
# ------------------------------------------------------------------------------
# dcmtk
# ------------------------------------------------------------------------------
DCMTK_VERSION=3.6.0
DCMTK_INSTALL_PREFIX=${__install_prefix}
DCMTK_SOURCE_URL=ftp://dicom.offis.de/pub/dicom/offis/software/dcmtk/dcmtk${DCMTK_VERSION//./}/dcmtk-${DCMTK_VERSION}.tar.gz

echo "=============================== DCMTK ================================"
if [ "${__download}" == "1" ]; then
    wget ${DCMTK_SOURCE_URL} -O ${__download_dir}/dcmtk-${DCMTK_VERSION}.tar.gz
fi

if [ "${__install}" == "1" ]; then
    tar xvf ${__download_dir}/dcmtk-${DCMTK_VERSION}.tar.gz
    pushd ${__build_dir}/dcmtk-${DCMTK_VERSION}

    cat << EOF > dcmtk-${DCMTK_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines ofstd/include/dcmtk/ofstd/offile.h ofstd/include/dcmtk/ofstd/offile.h
--- ofstd/include/dcmtk/ofstd/offile.h  2016-07-26 15:08:40.222470801 +0200
+++ ofstd/include/dcmtk/ofstd/offile.h  2016-07-26 15:08:05.218487436 +0200
@@ -196,7 +196,7 @@
   OFBool popen(const char *command, const char *modes)
   {
     if (file_) fclose();
-#ifdef _WIN32
+#if(defined(_WIN32) && !defined(__MINGW32__))
     file_ = _popen(command, modes);
 #else
     file_ = :: popen(command, modes);
@@ -258,7 +258,7 @@
     {
       if (popened_)
       {
-#ifdef _WIN32
+#if(defined(_WIN32) && !defined(__MINGW32__))
         result = _pclose(file_);
 #else
         result = :: pclose(file_);
diff -NurwB --strip-trailing-cr --suppress-common-lines CMakeLists.txt CMakeLists.txt
--- CMakeLists.txt  2016-07-27 16:45:48.057759327 +0200
+++ CMakeLists.txt  2016-07-27 16:50:08.993674806 +0200
@@ -222,6 +222,11 @@
 # define libraries that must be linked to most Windows applications
 IF(WIN32)
   SET(WIN32_STD_LIBRARIES ws2_32 netapi32 wsock32)
+  FOREACH(WIN32_LIB \${WIN32_STD_LIBRARIES})
+    SET(CMAKE_CXX_STANDARD_LIBRARIES "\${CMAKE_CXX_STANDARD_LIBRARIES} -l\${WIN32_LIB}" )
+  ENDFOREACH()
+  SET(CMAKE_CXX_FLAGS "-fpermissive \${CMAKE_CXX_FLAGS}")
+  
   # settings for Borland C++
   IF(CMAKE_CXX_COMPILER MATCHES bcc32)
     # to be checked: further settings required?
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmpstat/libsrc/CMakeLists.txt dcmpstat/libsrc/CMakeLists.txt
--- dcmpstat/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmpstat/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmpstat)
+
+IF ((TARGET dcmpstat) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmpstat dcmdsig dcmqrdb dcmqrdb dcmtls dcmsr dcmimgle)
+    TARGET_LINK_LIBRARIES(dcmpstat dcmdsig dcmqrdb dcmqrdb dcmtls dcmsr dcmimgle)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmdata/libsrc/CMakeLists.txt dcmdata/libsrc/CMakeLists.txt
--- dcmdata/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmdata/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmdata)
+
+IF ((TARGET dcmdata) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmdata oflog)
+    TARGET_LINK_LIBRARIES(dcmdata oflog)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmdata/libi2d/CMakeLists.txt dcmdata/libi2d/CMakeLists.txt
--- dcmdata/libi2d/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmdata/libi2d/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} libi2d)
+
+IF ((TARGET libi2d) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(libi2d dcmdata)
+    TARGET_LINK_LIBRARIES(libi2d dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmimgle/libsrc/CMakeLists.txt dcmimgle/libsrc/CMakeLists.txt
--- dcmimgle/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmimgle/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmimgle)
+
+IF ((TARGET dcmimgle) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmimgle dcmdata)
+    TARGET_LINK_LIBRARIES(dcmimgle dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmjpls/libsrc/CMakeLists.txt dcmjpls/libsrc/CMakeLists.txt
--- dcmjpls/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmjpls/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -6,3 +6,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmjpls)
+
+IF ((TARGET dcmjpls) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmjpls dcmjpeg charls)
+    TARGET_LINK_LIBRARIES(dcmjpls dcmjpeg charls)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmjpeg/libsrc/CMakeLists.txt dcmjpeg/libsrc/CMakeLists.txt
--- dcmjpeg/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmjpeg/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -6,3 +6,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmjpeg)
+
+IF ((TARGET dcmjpeg) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmjpeg dcmimgle ijg8 ijg12 ijg16)
+    TARGET_LINK_LIBRARIES(dcmjpeg dcmimgle ijg8 ijg12 ijg16)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmnet/li:q
bsrc/CMakeLists.txt dcmnet/libsrc/CMakeLists.txt
--- dcmnet/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmnet/libsrc/CMakeLists.txt    2016-07-27 17:42:30.272570054 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmnet)
+
+IF ((TARGET dcmnet) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmnet dcmdata)
+    TARGET_LINK_LIBRARIES(dcmnet dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmqrdb/libsrc/CMakeLists.txt dcmqrdb/libsrc/CMakeLists.txt
--- dcmqrdb/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmqrdb/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmqrdb)
+
+IF ((TARGET dcmqrdb) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmqrdb ofstd dcmdata dcmnet)
+    TARGET_LINK_LIBRARIES(dcmqrdb ofstd dcmdata dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmwlm/libsrc/CMakeLists.txt dcmwlm/libsrc/CMakeLists.txt
--- dcmwlm/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmwlm/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmwlm)
+
+IF ((TARGET dcmwlm) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmwlm dcmnet)
+    TARGET_LINK_LIBRARIES(dcmwlm dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmsign/libsrc/CMakeLists.txt dcmsign/libsrc/CMakeLists.txt
--- dcmsign/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmsign/libsrc/CMakeLists.txt   2016-07-27 17:42:30.272570054 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmdsig)
+
+IF ((TARGET dcmdsig) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmdsig dcmdata)
+    TARGET_LINK_LIBRARIES(dcmdsig dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmimage/libsrc/CMakeLists.txt dcmimage/libsrc/CMakeLists.txt
--- dcmimage/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmimage/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmimage)
+
+IF ((TARGET dcmimage) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmimage dcmimgle)
+    TARGET_LINK_LIBRARIES(dcmimage dcmimgle)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmtls/libsrc/CMakeLists.txt dcmtls/libsrc/CMakeLists.txt
--- dcmtls/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmtls/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmtls)
+
+IF ((TARGET dcmtls) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmtls dcmnet)
+    TARGET_LINK_LIBRARIES(dcmtls dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines oflog/libsrc/CMakeLists.txt oflog/libsrc/CMakeLists.txt
--- oflog/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
+++ oflog/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
@@ -10,3 +10,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} oflog)
+
+IF ((TARGET oflog) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(oflog ofstd)
+    TARGET_LINK_LIBRARIES(oflog ofstd)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmsr/libsrc/CMakeLists.txt dcmsr/libsrc/CMakeLists.txt
--- dcmsr/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
+++ dcmsr/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmsr)
+
+IF ((TARGET dcmsr) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmsr dcmdata)
+    TARGET_LINK_LIBRARIES(dcmsr dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines CMake/osconfig.h.in CMake/osconfig.h.in
--- CMake/osconfig.h.in       2016-09-04 22:05:16.440017095 +0200
+++ CMake/osconfig.h.in       2016-09-04 22:07:29.231895567 +0200
@@ -677,7 +677,10 @@
 #define PACKAGE_VERSION_SUFFIX "@DCMTK_PACKAGE_VERSION_SUFFIX@"
 
 /* Define to the version number of this package. */
-#define PACKAGE_VERSION_NUMBER "@DCMTK_PACKAGE_VERSION_NUMBER@"
+#define PACKAGE_VERSION_NUMBER @DCMTK_PACKAGE_VERSION_NUMBER@
+
+/* Define to the version number string of this package. */
+#define PACKAGE_VERSION_NUMBER_STRING "@DCMTK_PACKAGE_VERSION_NUMBER@"
 
 /* Define path separator */
 #define PATH_SEPARATOR '@PATH_SEPARATOR@'
diff -Nruwb dcmdata/include/dcmtk/dcmdata/dcuid.h dcmdata/include/dcmtk/dcmdata/dcuid.h
--- dcmdata/include/dcmtk/dcmdata/dcuid.h       2016-09-04 22:25:38.394956271 +0200
+++ dcmdata/include/dcmtk/dcmdata/dcuid.h       2016-09-04 22:31:28.442635450 +0200
@@ -171,10 +171,10 @@
  */
 
 /// implementation version name for this version of the toolkit
-#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME   "OFFIS_DCMTK_" PACKAGE_VERSION_NUMBER
+#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME   "OFFIS_DCMTK_" PACKAGE_VERSION_NUMBER_STRING
 
 /// implementation version name for this version of the toolkit, used for files received in "bit preserving" mode
-#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME2  "OFFIS_DCMBP_" PACKAGE_VERSION_NUMBER
+#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME2  "OFFIS_DCMBP_" PACKAGE_VERSION_NUMBER_STRING
EOF

    patch -f -N -i dcmtk-${DCMTK_VERSION}.patch -p0
    
    mkdir -p build
    pushd build
    
    cmake -DCMAKE_INSTALL_PREFIX=${DCMTK_INSTALL_PREFIX} \
          -DCMAKE_CXX_FLAGS=-fpermissive \
          -DCMAKE_SHARED_LINKER_FLAGS='-ltiff -lpng' \
          -DBUILD_SHARED_LIBS=ON \
          -DDCMTK_WITH_ZLIB=ON \
          -DDCMTK_WITH_PNG=ON \
          -DDCMTK_WITH_TIFF=ON \
          .. \
    || exit 1

    make -j${__build_proc_num} install || exit 1
    
    popd
    popd
    
    \rm -rf ${__build_dir}/dcmtk-${DCMTK_VERSION} \
            ${__download_dir}/dcmtk-${DCMTK_VERSION}.tar.gz
fi
