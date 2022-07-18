// based on https://github.com/PiInTheSky/pits/tree/master/tracker

#include <stdio.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include "modem_aprs.h"

// Sine wave table for tone generation
uint8_t _sine_table[] = {
#include "sine_table.h"
};

#define APRS_Preemphasis 0

#define attr(a) __attribute__((a))

#define packed attr(packed)

// APRS / AFSK variables

/* "converts" 4-char string to long int */
#define dw(a) (*(UL*)(a))

/* output buffer pointer */
int16_t *b = NULL;

void make_and_write_freq(UL cycles_per_bit, UL baud, UL lfreq, UL hfreq, int8_t High)
{
	// write 1 bit, which will be several values from the sine wave table
	static uint16_t phase  = 0;
	uint16_t step;

	if (High)
	{
		step = (512 * hfreq << 7) / (cycles_per_bit * baud);
		// printf("-");
	}
	else
	{
		step = (512 * lfreq << 7) / (cycles_per_bit * baud);
		// printf("_");
	}

	for (UL i=0; i<cycles_per_bit; i++)
	{
		// fwrite(&(_sine_table[(phase >> 7) & 0x1FF]), 1, 1, f);
		int16_t v = _sine_table[(phase >> 7) & 0x1FF] * 0x80 - 0x4000;
		if (!High && APRS_Preemphasis)
		{
			v *= 0.65;
		}
		else
		{
			v *= 1.3;
		}
		// int16_t v = _sine_table[(phase >> 7) & 0x1FF] * 0x100 - 0x8000;
		*(b++) = v;
		phase += step;
	}
}

void make_and_write_bit(UL cycles_per_bit, UL baud, UL lfreq, UL hfreq, unsigned char Bit, int BitStuffing)
{
	static int8_t bc = 0;
	static int8_t High = 0;

	if(BitStuffing)
	{
		if(bc >= 5)
		{
			High = !High;
			make_and_write_freq(cycles_per_bit, baud, lfreq, hfreq, High);
			bc = 0;
		}
	}
	else
	{
		bc = 0;
	}

	if (Bit)
	{
		// Stay with same frequency, but only for a max of 5 in a row
		bc++;
	}
	else
	{
		// 0 means swap frequency
		High = !High;
		bc = 0;
	}

	make_and_write_freq(cycles_per_bit, baud, lfreq, hfreq, High);
}


void make_and_write_byte(UL cycles_per_bit, UL baud, UL lfreq, UL hfreq, unsigned char Character, int BitStuffing)
{
	int i;

	// printf("%02X ", Character);

	for (i=0; i<8; i++)
	{
		make_and_write_bit(cycles_per_bit, baud, lfreq, hfreq, Character & 1, BitStuffing);
		Character >>= 1;
	}
}


/* makes wav file */
PyObject *makeafsk(UL freq, UL baud, UL lfreq, UL hfreq, unsigned char* Message[], int message_length[], int message_count, int total_message_length)
{
    printf("Building APRS packet\n");
    UL cycles_per_bit = freq / baud;
    UL cycles_per_byte = cycles_per_bit * 8;

    UL preamble_length = 128;
    UL postamble_length = 64;
    UL flags_before = 32;
    UL flags_after = 32;

    // Calculate size of file
    UL total_cycles = (cycles_per_byte * total_message_length) +
                   (cycles_per_byte * (flags_before + flags_after) * message_count) +
                   ((preamble_length + postamble_length) * cycles_per_bit * message_count);

    int16_t buffer[total_cycles+5];
    b = buffer;
    // Write preamble
    for (int j=0; j<message_count; j++)
    {
        for (UL i=0; i<flags_before; i++)
        {
            make_and_write_byte(cycles_per_bit, baud, lfreq, hfreq, 0x7E, 0);
        }

        // Create and write actual data
        for (int i=0; i<message_length[j]; i++)
        {
            make_and_write_byte(cycles_per_bit, baud, lfreq, hfreq, Message[j][i], 1);
        }

        for (UL i=0; i<flags_after; i++)
        {
            make_and_write_byte(cycles_per_bit, baud, lfreq, hfreq, 0x7E, 0);
        }

        // Write postamble
        for (UL i=0; i< postamble_length; i++)
        {
            make_and_write_freq(cycles_per_bit, baud, lfreq, hfreq, 0);
        }
    }

    return PyBytes_FromStringAndSize((const char *)buffer, total_cycles * 2 + 10);
}