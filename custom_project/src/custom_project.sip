%Module custom_projectsip

%Import aims.sip

namespace custom_project {

class Date
{
%TypeHeaderCode
#include <custom_project/custom_project.h>
%End
public:

  Date( int day, int month, int year );
  std::string str();

  int day;
  int month;
  int year;
};

}; // namespace custom_project
