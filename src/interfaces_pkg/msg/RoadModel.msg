std_msgs/Header header

bool left_detected
bool right_detected
bool center_valid
bool predicted

float32 left_x
float32 right_x
float32 center_x
float32 image_center_x

float32 lane_width_px

float32 lateral_error_px
float32 heading_error_rad
float32 curvature

float32 confidence

uint8 BRANCH_NONE=0
uint8 BRANCH_EXTRA_BOUNDARY=1
uint8 branch_flags
