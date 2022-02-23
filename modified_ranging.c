
/***********************************/
/*   VL53L5CX ULD get/set params   */
/***********************************/
/*
* This example shows the possibility of VL53L5CX to get/set params. It
* initializes the VL53L5CX ULD, set a configuration, and starts
* a ranging to capture 10 frames.
*
* In this example, we also suppose that the number of target per zone is
* set to 1 , and all output are enabled (see file platform.h).
*/

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "vl53l5cx_api.h"
#include <stdbool.h>

VL53L5CX_Configuration *ranging_ini(bool Is_4x4, int frame_rate)
{
	

	/*********************************/
	/*   VL53L5CX ranging variables  */
	/*********************************/

	uint8_t 				status, isAlive;
	uint32_t 				integration_time_ms;
	VL53L5CX_Configuration 	*p_dev;
	
	p_dev = malloc(sizeof(VL53L5CX_Configuration));

	/*********************************/
	/*   Power on sensor and init    */
	/*********************************/

	/* Initialize channel com */
	status = vl53l5cx_comms_init(&p_dev->platform);
	if(status)
	{
		printf("VL53L5CX comms init failed\n");
		exit(0);
	}

	printf("Starting examples with ULD version %s\n", VL53L5CX_API_REVISION);

	/* (Optional) Check if there is a VL53L5CX sensor connected */
	status = vl53l5cx_is_alive(p_dev, &isAlive);
	if(!isAlive || status)
	{
		printf("VL53L5CX not detected at requested address\n");
		exit(0);
	}

	/* (Mandatory) Init VL53L5CX sensor */
	status = vl53l5cx_init(p_dev);
	if(status)
	{
		printf("VL53L5CX ULD Loading failed\n");
		exit(0);
	}

	printf("VL53L5CX ULD ready ! (Version : %s)\n",
			VL53L5CX_API_REVISION);
			

	/*********************************/
	/*        Set some params        */
	/*********************************/

	/* Set resolution in 8x8. WARNING : As others settings depend to this
	 * one, it must be the first to use.
	 */
	if(Is_4x4)
	{
		status = vl53l5cx_set_resolution(p_dev, VL53L5CX_RESOLUTION_4X4);
	}
	else
	{
		status = vl53l5cx_set_resolution(p_dev, VL53L5CX_RESOLUTION_8X8);
	}
	if(status)
	{
		printf("vl53l5cx_set_resolution failed, status %u\n", status);
		exit(0);
	}

	/* Set ranging frequency to 10Hz.
	 * Using 4x4, min frequency is 1Hz and max is 60Hz
	 * Using 8x8, min frequency is 1Hz and max is 15Hz
	 */
	status = vl53l5cx_set_ranging_frequency_hz(p_dev, frame_rate);
	if(status)
	{
		printf("vl53l5cx_set_ranging_frequency_hz failed, status %u\n", status);
		exit(0);
	}

	/* Set target order to closest */
	status = vl53l5cx_set_target_order(p_dev, VL53L5CX_TARGET_ORDER_CLOSEST);
	if(status)
	{
		printf("vl53l5cx_set_target_order failed, status %u\n", status);
		exit(0);
	}

	/* Get current integration time */
	status = vl53l5cx_get_integration_time_ms(p_dev, &integration_time_ms);
	if(status)
	{
		printf("vl53l5cx_get_integration_time_ms failed, status %u\n", status);
		exit(0);
	}
	printf("Current integration time is : %d ms\n", integration_time_ms);
	
	status = vl53l5cx_start_ranging(p_dev);
	return p_dev;
}

struct Output{
	int16_t distance_mm[64];
	uint8_t target_status[64];
	uint8_t reflectance[64];
	};
	
struct Output *ranging(VL53L5CX_Configuration 	*p_dev, int mod_num)
{
	uint8_t 				status, loop, isAlive, isReady, i;
	uint32_t 				integration_time_ms;
	static VL53L5CX_ResultsData 	Results;		/* Results data from VL53L5CX */
	static struct Output					results_o;
	/*********************************/
	/*         Ranging loop          */
	/*********************************/



	loop = 0;
	while(loop < 1)
	{
		/* Use polling function to know when a new measurement is ready.
		 * Another way can be to wait for HW interrupt raised on PIN A3
		 * (GPIO 1) when a new measurement is ready */
 
		status = vl53l5cx_check_data_ready(p_dev, &isReady);

		if(isReady)
		{
			vl53l5cx_get_ranging_data(p_dev, &Results);

			/* As the sensor is set in 8x8 mode, we have a total
			 * of 64 zones to print. For this example, only the data of
			 * first zone are print */
			/*
			printf("Print data no : %3u\n", p_dev->streamcount);
			for(i = 0; i < mod_num*mod_num; i++)
			{
				printf("Zone : %3d, Status : %3u, Distance : %4d mm\n",
					i,
					Results.target_status[VL53L5CX_NB_TARGET_PER_ZONE*i],
					Results.distance_mm[VL53L5CX_NB_TARGET_PER_ZONE*i]);
			}
			printf("\n");
			*/
			loop++;
		}

		/* Wait a few ms to avoid too high polling (function in platform
		 * file, not in API) */
		WaitMs(&p_dev->platform, 5);
	}
	memcpy(results_o.distance_mm, Results.distance_mm, sizeof Results.distance_mm);
	memcpy(results_o.target_status, Results.target_status, sizeof Results.target_status);
	memcpy(results_o.reflectance, Results.reflectance, sizeof Results.reflectance);

	return &results_o;
}
int StopRanging(VL53L5CX_Configuration 	*p_dev)
{
	int status;
	
	status = vl53l5cx_stop_ranging(p_dev);
	printf("End of ranging\n");
	
	return status;
}
int main()
{
	int status,i;
	struct Output *p_result;
	VL53L5CX_Configuration *p_dev;
	p_dev = ranging_ini(true,30);
	p_result = ranging(p_dev,4);
	status = StopRanging(p_dev);
	free(p_dev);

	for(i = 0; i < 16; i++)
	{
		printf("Distance : %4d , Reflectance : %3u \n",p_result->distance_mm[i],p_result->reflectance[i]);
	}
	
	return 0;
}
