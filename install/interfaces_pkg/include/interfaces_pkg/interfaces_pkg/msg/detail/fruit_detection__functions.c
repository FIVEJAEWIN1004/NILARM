// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from interfaces_pkg:msg/FruitDetection.idl
// generated code does not contain a copyright notice
#include "interfaces_pkg/msg/detail/fruit_detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `quality`
#include "rosidl_runtime_c/string_functions.h"

bool
interfaces_pkg__msg__FruitDetection__init(interfaces_pkg__msg__FruitDetection * msg)
{
  if (!msg) {
    return false;
  }
  // x
  // y
  // z
  // quality
  if (!rosidl_runtime_c__String__init(&msg->quality)) {
    interfaces_pkg__msg__FruitDetection__fini(msg);
    return false;
  }
  // confidence
  return true;
}

void
interfaces_pkg__msg__FruitDetection__fini(interfaces_pkg__msg__FruitDetection * msg)
{
  if (!msg) {
    return;
  }
  // x
  // y
  // z
  // quality
  rosidl_runtime_c__String__fini(&msg->quality);
  // confidence
}

bool
interfaces_pkg__msg__FruitDetection__are_equal(const interfaces_pkg__msg__FruitDetection * lhs, const interfaces_pkg__msg__FruitDetection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // x
  if (lhs->x != rhs->x) {
    return false;
  }
  // y
  if (lhs->y != rhs->y) {
    return false;
  }
  // z
  if (lhs->z != rhs->z) {
    return false;
  }
  // quality
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->quality), &(rhs->quality)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  return true;
}

bool
interfaces_pkg__msg__FruitDetection__copy(
  const interfaces_pkg__msg__FruitDetection * input,
  interfaces_pkg__msg__FruitDetection * output)
{
  if (!input || !output) {
    return false;
  }
  // x
  output->x = input->x;
  // y
  output->y = input->y;
  // z
  output->z = input->z;
  // quality
  if (!rosidl_runtime_c__String__copy(
      &(input->quality), &(output->quality)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  return true;
}

interfaces_pkg__msg__FruitDetection *
interfaces_pkg__msg__FruitDetection__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__FruitDetection * msg = (interfaces_pkg__msg__FruitDetection *)allocator.allocate(sizeof(interfaces_pkg__msg__FruitDetection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__msg__FruitDetection));
  bool success = interfaces_pkg__msg__FruitDetection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__msg__FruitDetection__destroy(interfaces_pkg__msg__FruitDetection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__msg__FruitDetection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__msg__FruitDetection__Sequence__init(interfaces_pkg__msg__FruitDetection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__FruitDetection * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__msg__FruitDetection)) {
      return false;
    }
    data = (interfaces_pkg__msg__FruitDetection *)allocator.zero_allocate(size, sizeof(interfaces_pkg__msg__FruitDetection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__msg__FruitDetection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__msg__FruitDetection__fini(&data[i - 1]);
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
interfaces_pkg__msg__FruitDetection__Sequence__fini(interfaces_pkg__msg__FruitDetection__Sequence * array)
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
      interfaces_pkg__msg__FruitDetection__fini(&array->data[i]);
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

interfaces_pkg__msg__FruitDetection__Sequence *
interfaces_pkg__msg__FruitDetection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__msg__FruitDetection__Sequence * array = (interfaces_pkg__msg__FruitDetection__Sequence *)allocator.allocate(sizeof(interfaces_pkg__msg__FruitDetection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__msg__FruitDetection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__msg__FruitDetection__Sequence__destroy(interfaces_pkg__msg__FruitDetection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__msg__FruitDetection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__msg__FruitDetection__Sequence__are_equal(const interfaces_pkg__msg__FruitDetection__Sequence * lhs, const interfaces_pkg__msg__FruitDetection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__msg__FruitDetection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__msg__FruitDetection__Sequence__copy(
  const interfaces_pkg__msg__FruitDetection__Sequence * input,
  interfaces_pkg__msg__FruitDetection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__msg__FruitDetection)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__msg__FruitDetection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__msg__FruitDetection * data =
      (interfaces_pkg__msg__FruitDetection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__msg__FruitDetection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__msg__FruitDetection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__msg__FruitDetection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
