// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_pkg:action/DumpBasket.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/action/dump_basket.h"


#ifndef INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__STRUCT_H_
#define INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_Goal
{
  uint8_t structure_needs_at_least_one_member;
} interfaces_pkg__action__DumpBasket_Goal;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_Goal.
typedef struct interfaces_pkg__action__DumpBasket_Goal__Sequence
{
  interfaces_pkg__action__DumpBasket_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_Goal__Sequence;

// Constants defined in the message

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_Result
{
  bool success;
  float duration_sec;
} interfaces_pkg__action__DumpBasket_Result;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_Result.
typedef struct interfaces_pkg__action__DumpBasket_Result__Sequence
{
  interfaces_pkg__action__DumpBasket_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_Result__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'phase'
#include "rosidl_runtime_c/string.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_Feedback
{
  /// "tilting", "pouring", "returning"
  rosidl_runtime_c__String phase;
} interfaces_pkg__action__DumpBasket_Feedback;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_Feedback.
typedef struct interfaces_pkg__action__DumpBasket_Feedback__Sequence
{
  interfaces_pkg__action__DumpBasket_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_Feedback__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "interfaces_pkg/action/detail/dump_basket__struct.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  interfaces_pkg__action__DumpBasket_Goal goal;
} interfaces_pkg__action__DumpBasket_SendGoal_Request;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_SendGoal_Request.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence
{
  interfaces_pkg__action__DumpBasket_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} interfaces_pkg__action__DumpBasket_SendGoal_Response;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_SendGoal_Response.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence
{
  interfaces_pkg__action__DumpBasket_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  interfaces_pkg__action__DumpBasket_SendGoal_Event__request__MAX_SIZE = 1
};
// response
enum
{
  interfaces_pkg__action__DumpBasket_SendGoal_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Event
{
  service_msgs__msg__ServiceEventInfo info;
  interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence request;
  interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence response;
} interfaces_pkg__action__DumpBasket_SendGoal_Event;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_SendGoal_Event.
typedef struct interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence
{
  interfaces_pkg__action__DumpBasket_SendGoal_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} interfaces_pkg__action__DumpBasket_GetResult_Request;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_GetResult_Request.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence
{
  interfaces_pkg__action__DumpBasket_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__struct.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Response
{
  int8_t status;
  interfaces_pkg__action__DumpBasket_Result result;
} interfaces_pkg__action__DumpBasket_GetResult_Response;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_GetResult_Response.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence
{
  interfaces_pkg__action__DumpBasket_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
// already included above
// #include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  interfaces_pkg__action__DumpBasket_GetResult_Event__request__MAX_SIZE = 1
};
// response
enum
{
  interfaces_pkg__action__DumpBasket_GetResult_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Event
{
  service_msgs__msg__ServiceEventInfo info;
  interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence request;
  interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence response;
} interfaces_pkg__action__DumpBasket_GetResult_Event;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_GetResult_Event.
typedef struct interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence
{
  interfaces_pkg__action__DumpBasket_GetResult_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__struct.h"

/// Struct defined in action/DumpBasket in the package interfaces_pkg.
typedef struct interfaces_pkg__action__DumpBasket_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  interfaces_pkg__action__DumpBasket_Feedback feedback;
} interfaces_pkg__action__DumpBasket_FeedbackMessage;

// Struct for a sequence of interfaces_pkg__action__DumpBasket_FeedbackMessage.
typedef struct interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence
{
  interfaces_pkg__action__DumpBasket_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_PKG__ACTION__DETAIL__DUMP_BASKET__STRUCT_H_
