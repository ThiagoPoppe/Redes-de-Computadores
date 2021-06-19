#ifndef LOCATION_H
#define LOCATION_H

#define MAX_NUM_LOCATIONS 50

typedef struct point {
    int x;
    int y;
} Point2D_t;

typedef struct location {
    int size;
    Point2D_t array[MAX_NUM_LOCATIONS];
} LocationArray_t;

// Function to create the location array
void create_location_array(LocationArray_t* location_array);

// Function to add a new location
// The operation status will be saved on the string "status"
void add_location(LocationArray_t* location_array, Point2D_t coord, char *status); 

// Function to shift the location array to the left given an index
void shift_left(LocationArray_t* location_array, int idx);

// Function to remove a location
// The operation status will be saved on the string "status"
void remove_location(LocationArray_t* location_array, Point2D_t coord, char *status);

// Function to represent the location array as a string (X1 Y1 X2 Y2 ... Xn Yn)
void location_array_to_string(LocationArray_t* location_array, char *str);

// Function to get the closest location
// The operation status will be saved on the string "status"
void get_closest_location(LocationArray_t* location_array, Point2D_t coord, char *status);

#endif