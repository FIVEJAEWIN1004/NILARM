// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_pkg:action/Harvest.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/action/harvest.h"


#ifndef INTERFACES_PKG__ACTION__DETAIL__HARVEST__STRUCT_H_
#define INTERFACES_PKG__ACTION__DETAIL__HARVEST__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_Goal
{
  /// 이번에 몇 개 수확할지 목표 !git
  int32_t target_count;
} interfaces_pkg__action__Harvest_Goal;

// Struct for a sequence of interfaces_pkg__action__Harvest_Goal.
typedef struct interfaces_pkg__action__Harvest_Goal__Sequence
{
  interfaces_pkg__action__Harvest_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_Goal__Sequence;

// Constants defined in the message

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_Result
{
  bool success;
  /// 실제로 수확한 개수
  int32_t harvested_count;
} interfaces_pkg__action__Harvest_Result;

// Struct for a sequence of interfaces_pkg__action__Harvest_Result.
typedef struct interfaces_pkg__action__Harvest_Result__Sequence
{
  interfaces_pkg__action__Harvest_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_Result__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'status'
#include "rosidl_runtime_c/string.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_Feedback
{
  /// 지금까지 몇 개 땄는지 !!
  int32_t current_count;
  /// "searching", "grasping", "placing" 등
  rosidl_runtime_c__String status;
} interfaces_pkg__action__Harvest_Feedback;

// Struct for a sequence of interfaces_pkg__action__Harvest_Feedback.
typedef struct interfaces_pkg__action__Harvest_Feedback__Sequence
{
  interfaces_pkg__action__Harvest_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_Feedback__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "interfaces_pkg/action/detail/harvest__struct.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  interfaces_pkg__action__Harvest_Goal goal;
} interfaces_pkg__action__Harvest_SendGoal_Request;

// Struct for a sequence of interfaces_pkg__action__Harvest_SendGoal_Request.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Request__Sequence
{
  interfaces_pkg__action__Harvest_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_SendGoal_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} interfaces_pkg__action__Harvest_SendGoal_Response;

// Struct for a sequence of interfaces_pkg__action__Harvest_SendGoal_Response.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Response__Sequence
{
  interfaces_pkg__action__Harvest_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_SendGoal_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  interfaces_pkg__action__Harvest_SendGoal_Event__request__MAX_SIZE = 1
};
// response
enum
{
  interfaces_pkg__action__Harvest_SendGoal_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Event
{
  service_msgs__msg__ServiceEventInfo info;
  interfaces_pkg__action__Harvest_SendGoal_Request__Sequence request;
  interfaces_pkg__action__Harvest_SendGoal_Response__Sequence response;
} interfaces_pkg__action__Harvest_SendGoal_Event;

// Struct for a sequence of interfaces_pkg__action__Harvest_SendGoal_Event.
typedef struct interfaces_pkg__action__Harvest_SendGoal_Event__Sequence
{
  interfaces_pkg__action__Harvest_SendGoal_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_SendGoal_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} interfaces_pkg__action__Harvest_GetResult_Request;

// Struct for a sequence of interfaces_pkg__action__Harvest_GetResult_Request.
typedef struct interfaces_pkg__action__Harvest_GetResult_Request__Sequence
{
  interfaces_pkg__action__Harvest_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_GetResult_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_GetResult_Response
{
  int8_t status;
  interfaces_pkg__action__Harvest_Result result;
} interfaces_pkg__action__Harvest_GetResult_Response;

// Struct for a sequence of interfaces_pkg__action__Harvest_GetResult_Response.
typedef struct interfaces_pkg__action__Harvest_GetResult_Response__Sequence
{
  interfaces_pkg__action__Harvest_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_GetResult_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
// already included above
// #include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  interfaces_pkg__action__Harvest_GetResult_Event__request__MAX_SIZE = 1
};
// response
enum
{
  interfaces_pkg__action__Harvest_GetResult_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_GetResult_Event
{
  service_msgs__msg__ServiceEventInfo info;
  interfaces_pkg__action__Harvest_GetResult_Request__Sequence request;
  interfaces_pkg__action__Harvest_GetResult_Response__Sequence response;
} interfaces_pkg__action__Harvest_GetResult_Event;

// Struct for a sequence of interfaces_pkg__action__Harvest_GetResult_Event.
typedef struct interfaces_pkg__action__Harvest_GetResult_Event__Sequence
{
  interfaces_pkg__action__Harvest_GetResult_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_GetResult_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "interfaces_pkg/action/detail/harvest__struct.h"

/// Struct defined in action/Harvest in the package interfaces_pkg.
typedef struct interfaces_pkg__action__Harvest_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  interfaces_pkg__action__Harvest_Feedback feedback;
} interfaces_pkg__action__Harvest_FeedbackMessage;

// Struct for a sequence of interfaces_pkg__action__Harvest_FeedbackMessage.
typedef struct interfaces_pkg__action__Harvest_FeedbackMessage__Sequence
{
  interfaces_pkg__action__Harvest_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__Harvest_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_PKG__ACTION__DETAIL__HARVEST__STRUCT_H_
