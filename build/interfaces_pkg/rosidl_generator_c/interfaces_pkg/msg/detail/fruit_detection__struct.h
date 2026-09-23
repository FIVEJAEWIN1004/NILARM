// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_pkg:msg/FruitDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/fruit_detection.h"


#ifndef INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__STRUCT_H_
#define INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'quality'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/FruitDetection in the package interfaces_pkg.
typedef struct interfaces_pkg__msg__FruitDetection
{
  /// 카메라/팔 기준 상대좌표 (m)
  float x;
  float y;
  float z;
  /// "ripe"(익음) 또는 "bad"(불량)
  rosidl_runtime_c__String quality;
  /// 탐지 신뢰도 0.0~1.0
  float confidence;
} interfaces_pkg__msg__FruitDetection;

// Struct for a sequence of interfaces_pkg__msg__FruitDetection.
typedef struct interfaces_pkg__msg__FruitDetection__Sequence
{
  interfaces_pkg__msg__FruitDetection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__msg__FruitDetection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__STRUCT_H_
