// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_pkg:msg/MissionState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/mission_state.h"


#ifndef INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__STRUCT_H_
#define INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'state'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/MissionState in the package interfaces_pkg.
typedef struct interfaces_pkg__msg__MissionState
{
  /// "IDLE","NAV_TO_LOADING","HARVEST","DUMP","CHECK_GOAL","NAV_TO_UNLOAD","COMPLETE","ERROR"
  rosidl_runtime_c__String state;
  /// 지금까지 누적 수확 개수
  int32_t harvested_total;
  /// 목표 수확 개수
  int32_t goal_count;
} interfaces_pkg__msg__MissionState;

// Struct for a sequence of interfaces_pkg__msg__MissionState.
typedef struct interfaces_pkg__msg__MissionState__Sequence
{
  interfaces_pkg__msg__MissionState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__msg__MissionState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_PKG__MSG__DETAIL__MISSION_STATE__STRUCT_H_
