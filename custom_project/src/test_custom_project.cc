#include <custom_project/custom_project.h>
#include <iostream>
#include <cstdlib>

using namespace std;

int main( int argc, const char *argv[] )
{
  if ( argc != 4 ) {
    cerr << "Usage: " << argv[0] << " day month year" << endl;
    return EXIT_FAILURE;
  }
  custom_project::Date d( atoi( argv[1] ), atoi( argv[2] ), atoi( argv[3] ) );
  cout << d.str() << endl;
  return EXIT_SUCCESS;
}
