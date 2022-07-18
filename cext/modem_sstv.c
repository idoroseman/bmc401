#include"modem_sstv.h"

// Martin M1 modem
// derivitive work based on KI4MCW, PA3BYA
// source: https://github.com/AgriVision/pisstv/blob/master/pisstv.c

#define RATE   11025
#define MAXRATE   22050
#define BITS   16
#define CHANS  1
#define VOLPCT 20

#define COLS 320
#define ROWS 256
#define CHANNELS 3

/* output buffer pointer */
int16_t    *g_audio_ptr = NULL;
uint32_t   g_scale, g_samples ;
double     g_twopioverrate , g_uspersample ;
double     g_theta, g_fudge ;
uint16_t   g_rate;

// playtone -- Add waveform info to audio data. New waveform data is
//             added in a phase-continuous manner according to the
//             audio frequency and duration provided. Note that the
//             audio is still in a purely hypothetical state - the
//             format of the output file is not determined until
//             the file is written, at the end of the process.
//             Also, yes, a nod to Tom Hanks.

void playtone( uint16_t tonefreq , double tonedur )
{
    uint16_t tonesamples, voltage, i ;
    double   deltatheta ;

    tonedur += g_fudge ;
    tonesamples = ( tonedur / g_uspersample ) + 0.5 ;
    deltatheta = g_twopioverrate * tonefreq ;

    for ( i=1 ; i<=tonesamples ; i++ )
    {
        if ( tonefreq == 0 )
        {
            *(g_audio_ptr++) = 0 ;
        }
        else
        {
            voltage =     0 + (int)( sin( g_theta ) * g_scale ) ;
            *(g_audio_ptr++) = voltage ;
            g_theta += deltatheta ;
        }
    }

    g_fudge = tonedur - ( tonesamples * g_uspersample ) ;
}  // end playtone


// addvisheader -- Add the specific audio tones that make up the
//                 Martin 1 VIS header to the audio data. Basically,
//                 this just means lots of calls to playtone().

void addvisheader()
{
    printf( "Adding VIS header to audio data.\n" ) ;

    // bit of silence
    playtone(    0 , 500000 ) ;

    // attention tones
    playtone( 1900 , 100000 ) ; // you forgot this one
    playtone( 1500 , 100000 ) ;
    playtone( 1900 , 100000 ) ;
    playtone( 1500 , 100000 ) ;
    playtone( 2300 , 100000 ) ;
    playtone( 1500 , 100000 ) ;
    playtone( 2300 , 100000 ) ;
    playtone( 1500 , 100000 ) ;

    // VIS lead, break, mid, start
    playtone( 1900 , 300000 ) ;
    playtone( 1200 ,  10000 ) ;
//    playtone( 1500 , 300000 ) ;
    playtone( 1900 , 300000 ) ;
    playtone( 1200 ,  30000 ) ;

    // VIS data bits (Martin 1)
    playtone( 1300 ,  30000 ) ;
    playtone( 1300 ,  30000 ) ;
    playtone( 1100 ,  30000 ) ;
    playtone( 1100 ,  30000 ) ;
    playtone( 1300 ,  30000 ) ;
    playtone( 1100 ,  30000 ) ;
    playtone( 1300 ,  30000 ) ;
    playtone( 1100 ,  30000 ) ;

    // VIS stop
    playtone( 1200 ,  30000 ) ;

    printf( "Done adding VIS header to audio data.\n" ) ;

} // end addvisheader


// addvistrailer -- Add tones for VIS trailer to audio stream.
//                  More calls to playtone().

void addvistrailer ()
{
    printf( "Adding VIS trailer to audio data.\n" ) ;

    playtone( 2300 , 300000 ) ;
    playtone( 1200 ,  10000 ) ;
    playtone( 2300 , 100000 ) ;
    playtone( 1200 ,  30000 ) ;

    // bit of silence
    playtone(    0 , 500000 ) ;

    printf( "Done adding VIS trailer to audio data.\n" ) ;
}


// toneval -- Map an 8-bit value to a corresponding number between
//            1500 and 2300, on a simple linear scale. This is used
//            to map an 8-bit color intensity (I know, wrong word)
//            to an audio frequency. This is the lifeblood of SSTV.

uint16_t toneval ( uint8_t colorval )
{
    return ( ( 800 * colorval ) / 256 ) + 1500 ;
}


// buildaudio -- Primary code for converting image data to audio.
//               Reads color data for individual pixels from a libGD
//               object, calls toneval() to convert the color data
//               to an audio frequency, then calls playtone() to add
//               that to the audio data. This routine assumes an image
//               320 wide x 256 tall x 24 bit colorspace (8 bits each
//               for R, G, and B).
//
//               In Martin 1, the image data is sent one row at a time,
//               once for green, once for blue, and once for red. There
//               is a separator tone between each channel's audio, and
//               a sync tone at the beginning of each new row. This
//               routine handles the sep/sync details as well.

void buildaudio (PyArrayObject *image)
{
    uint16_t x , y , k ;
    uint8_t r[COLS], g[COLS], b[COLS] ;

    printf( "Adding image to audio data.\n" ) ;

    for ( y=0 ; y<ROWS ; y++ )
    {
//        printf( "Row [%d] Sample [%d].\n" , y , g_samples ) ;

        // read image data
        for ( x=0 ; x<COLS ; x++ )
        {
            // get color data
            r[x] = *(unsigned char *)PyArray_GETPTR3(image, y, x, 0);
            g[x] = *(unsigned char *)PyArray_GETPTR3(image, y, x, 1);
            b[x] = *(unsigned char *)PyArray_GETPTR3(image, y, x, 2);
        }

        // add row markers to audio
        // sync
        playtone( 1200 , 4862 ) ;
        // porch
        playtone( 1500 ,  572 ) ;

        // each pixel is 457.6us long in Martin 1

        // add audio for green channel for this row
        for ( k=0 ; k<320 ; k++ )
        { playtone( toneval( g[k] ) , 457.6 ) ; }

        // separator tone
        playtone( 1500 , 572 ) ;

        // bloo channel
        for ( k=0 ; k<320 ; k++ )
        { playtone( toneval( b[k] ) , 457.6 ) ; }

        playtone( 1500 , 572 ) ;

        // red channel
        for ( k=0 ; k<320 ; k++ )
        { playtone( toneval( r[k] ) , 457.6 ) ; }

        playtone( 1500 , 572 ) ;

    }  // end for y

    printf( "Done adding image to audio data.\n" ) ;

}  // end buildaudio

// ----------------------------------------------------------------------------

PyObject *makesstv(int samplerate, PyArrayObject *image) {

    // assign values to globals

    double temp1, temp2, temp3 ;
    temp1 = (double)( 1 << (BITS - 1) ) ;
    temp2 = VOLPCT / 100.0 ;
    temp3 = temp1 * temp2 ;
    g_scale = (uint32_t)temp3 ;

    g_rate = samplerate;
    g_twopioverrate = 2.0 * M_PI / g_rate ;
    g_uspersample = 1000000.0 / (double)g_rate ;

    g_theta = 0.0 ;
    g_samples = 0.0 ;
    g_fudge = 0.0 ;

    printf( "Constants check:\n" ) ;
    printf( "      rate = %d\n" , g_rate ) ;
    printf( "      BITS = %d\n" , BITS ) ;
    printf( "    VOLPCT = %d\n" , VOLPCT ) ;
    printf( "     scale = %d\n" , g_scale ) ;
    printf( "   us/samp = %f\n" , g_uspersample ) ;
    printf( "   2p/rate = %f\n\n" , g_twopioverrate ) ;

    double total_us_header = 2210000;
    double total_us_trailer = 940000;
    double total_us_body = ROWS * ( 6006 + COLS * 457.6 * CHANNELS );
    printf( "total duration %.1f seconds\n" , (total_us_header + total_us_body + total_us_trailer ) / 1000000 ) ;

    uint32_t total_cycles = (total_us_header + total_us_body + total_us_trailer + 500000) * g_rate / 1000000;
    printf("%d samples\n", total_cycles);
    int16_t buffer[total_cycles+10];
    g_audio_ptr = buffer;

    addvisheader() ;
    buildaudio(image) ;
    addvistrailer() ;

    return PyBytes_FromStringAndSize((const char *)buffer, total_cycles*2 );
}