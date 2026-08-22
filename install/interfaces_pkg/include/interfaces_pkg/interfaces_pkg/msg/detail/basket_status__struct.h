// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/basket_status.h"


#ifndef INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_H_
#define INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/BasketStatus in the package interfaces_pkg.
typedef struct interfaces_pkg__msg__BasketStatus
{
  /// 현재 적재된 개수
  int32_t weight;
  /// 소형바구니 최대 용량
  int32_t maxweight;
  /// count >= capacity 여부
  bool is_full;
} interfaces_pkg__msg__BasketStatus;

// Struct for a sequence of interfaces_pkg__msg__BasketStatus.
typedef struct interfaces_pkg__msg__BasketStatus__Sequence
{
  interfaces_pkg__msg__BasketStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_pkg__msg__BasketStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_H_
