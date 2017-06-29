#include <custom_project/custom_project.h>
#include <sstream>

using namespace std;

namespace custom_project {

Date::Date( int d, int m, int y ) : day( d ), month( m ), year( y ) {}
string Date::str()
{
  stringstream o;
  o << day << "/" << month << "/" << year;
  return o.str();
}

} // namespace custom_project
