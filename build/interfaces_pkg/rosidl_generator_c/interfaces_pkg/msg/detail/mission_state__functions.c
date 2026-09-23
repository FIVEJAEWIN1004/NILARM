// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from interfaces_pkg:msg/MissionState.idl
// generated code does not contain a copyright notice
#include "interfaces_pkg/msg/detail/mission_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `state`
#include "rosidl_runtime_c/string_functions.h"

bool
interfaces_pkg__msg__MissionState__init(interfaces_pkg__msg__MissionState * msg)
{
  if (!msg) {
    return false;
  }
  // state
  if (!rosidl_runtime_c__String__init(&msg->state)) {
    interfaces_pkg__msg__MissionState__fini(msg);
    return false;
  }
  // harvested_total
  // goal_count
  return true;
}

void
interfaces_pkg__msg__MissionState__fini(interfaces_pkg__msg__MissionState * msg)
{
  if (!msg) {
    return;
  }
  // state
  rosidl_runtime_c__String__fini(&msg->state);
  // harvested_total
  // goal_count
}

bool
interfaces_pkg__msg__MissionState__are_equal(const interfaces_pkg__msg__MissionState * lhs, const interfaces_pkg__msg__MissionState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // state
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->state), &(rhs->state)))
  {
    return false;
  }
  // harvested_total
  if (lhs->harvested_total != rhs->harvested_total) {
    return false;
  }
  // goal_count
  if (lhs->goal_count != rhs->goal_count) {
    return false;
  }
  return true;
}

bool
interfaces_pkg__msg__MissionState__copy(
  const interfaces_pkg__msg__MissionState * input,
  interfaces_pkg__msg__MissionState * output)
{
  if (!input || !output) {
    return false;
  }
  // state
  if (!rosidl_runtime_c__String__copy(
      &(input->state), &(output->state)))
  {
    return false;
  }
  // harvested_total
  output->harvested_total = input->harvested_total;
  // goal_count
  output->goal_count = input->goal_count;
  return true;
}

interfaces_pkg__msg__MissionState *
interfaces_pkg__msg__MissionState__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__MissionState * msg = (interfaces_pkg__msg__MissionState *)allocator.allocate(sizeof(interfaces_pkg__msg__MissionState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__msg__MissionState));
  bool success = interfaces_pkg__msg__MissionState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__msg__MissionState__destroy(interfaces_pkg__msg__MissionState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__msg__MissionState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__msg__MissionState__Sequence__init(interfaces_pkg__msg__MissionState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__MissionState * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__msg__MissionState)) {
      return false;
    }
    data = (interfaces_pkg__msg__MissionState *)allocator.zero_allocate(size, sizeof(interfaces_pkg__msg__MissionState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__msg__MissionState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__msg__MissionState__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
interfaces_pkg__msg__MissionState__Sequence__fini(interfaces_pkg__msg__MissionState__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      interfaces_pkg__msg__MissionState__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

interfaces_pkg__msg__MissionState__Sequence *
interfaces_pkg__msg__MissionState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__MissionState__Sequence * array = (interfaces_pkg__msg__MissionState__Sequence *)allocator.allocate(sizeof(interfaces_pkg__msg__MissionState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__msg__MissionState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__msg__MissionState__Sequence__destroy(interfaces_pkg__msg__MissionState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__msg__MissionState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__msg__MissionState__Sequence__are_equal(const interfaces_pkg__msg__MissionState__Sequence * lhs, const interfaces_pkg__msg__MissionState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__msg__MissionState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__msg__MissionState__Sequence__copy(
  const interfaces_pkg__msg__MissionState__Sequence * input,
  interfaces_pkg__msg__MissionState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__msg__MissionState)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__msg__MissionState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__msg__MissionState * data =
      (interfaces_pkg__msg__MissionState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__msg__MissionState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__msg__MissionState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__msg__MissionState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
