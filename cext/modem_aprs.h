#include <Python.h>

typedef unsigned int	UI;
typedef unsigned int	UL;
typedef unsigned short int	US;
typedef unsigned char	UC;
typedef signed int		SI;
typedef signed long int	SL;
typedef signed short int	SS;
typedef signed char	SC;

PyObject * makeafsk(UL freq, UL baud, UL lfreq, UL hfreq, unsigned char* Message[], int message_length[], int message_count, int total_message_length);