#ifndef CUSTOM_PROJECT_H
#define CUSTOM_PROJECT_H

#include <string>

namespace custom_project {

class Date
{
public:

  Date( int day, int month, int year );
  std::string str();

  int day, month, year;
};

} // namespace custom_project

#endif // CUSTOM_PROJECT_H
