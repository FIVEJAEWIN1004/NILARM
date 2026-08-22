// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from interfaces_pkg:action/DumpBasket.idl
// generated code does not contain a copyright notice
#include "interfaces_pkg/action/detail/dump_basket__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
interfaces_pkg__action__DumpBasket_Goal__init(interfaces_pkg__action__DumpBasket_Goal * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
interfaces_pkg__action__DumpBasket_Goal__fini(interfaces_pkg__action__DumpBasket_Goal * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
interfaces_pkg__action__DumpBasket_Goal__are_equal(const interfaces_pkg__action__DumpBasket_Goal * lhs, const interfaces_pkg__action__DumpBasket_Goal * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // structure_needs_at_least_one_member
  if (lhs->structure_needs_at_least_one_member != rhs->structure_needs_at_least_one_member) {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Goal__copy(
  const interfaces_pkg__action__DumpBasket_Goal * input,
  interfaces_pkg__action__DumpBasket_Goal * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

interfaces_pkg__action__DumpBasket_Goal *
interfaces_pkg__action__DumpBasket_Goal__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Goal * msg = (interfaces_pkg__action__DumpBasket_Goal *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Goal), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_Goal));
  bool success = interfaces_pkg__action__DumpBasket_Goal__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_Goal__destroy(interfaces_pkg__action__DumpBasket_Goal * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_Goal__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_Goal__Sequence__init(interfaces_pkg__action__DumpBasket_Goal__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Goal * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Goal)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_Goal *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_Goal), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_Goal__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_Goal__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_Goal__Sequence__fini(interfaces_pkg__action__DumpBasket_Goal__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_Goal__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_Goal__Sequence *
interfaces_pkg__action__DumpBasket_Goal__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Goal__Sequence * array = (interfaces_pkg__action__DumpBasket_Goal__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Goal__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_Goal__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_Goal__Sequence__destroy(interfaces_pkg__action__DumpBasket_Goal__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_Goal__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_Goal__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_Goal__Sequence * lhs, const interfaces_pkg__action__DumpBasket_Goal__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Goal__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Goal__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_Goal__Sequence * input,
  interfaces_pkg__action__DumpBasket_Goal__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Goal)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_Goal);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_Goal * data =
      (interfaces_pkg__action__DumpBasket_Goal *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_Goal__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_Goal__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Goal__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
interfaces_pkg__action__DumpBasket_Result__init(interfaces_pkg__action__DumpBasket_Result * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // duration_sec
  return true;
}

void
interfaces_pkg__action__DumpBasket_Result__fini(interfaces_pkg__action__DumpBasket_Result * msg)
{
  if (!msg) {
    return;
  }
  // success
  // duration_sec
}

bool
interfaces_pkg__action__DumpBasket_Result__are_equal(const interfaces_pkg__action__DumpBasket_Result * lhs, const interfaces_pkg__action__DumpBasket_Result * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // duration_sec
  if (lhs->duration_sec != rhs->duration_sec) {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Result__copy(
  const interfaces_pkg__action__DumpBasket_Result * input,
  interfaces_pkg__action__DumpBasket_Result * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // duration_sec
  output->duration_sec = input->duration_sec;
  return true;
}

interfaces_pkg__action__DumpBasket_Result *
interfaces_pkg__action__DumpBasket_Result__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Result * msg = (interfaces_pkg__action__DumpBasket_Result *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Result), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_Result));
  bool success = interfaces_pkg__action__DumpBasket_Result__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_Result__destroy(interfaces_pkg__action__DumpBasket_Result * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_Result__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_Result__Sequence__init(interfaces_pkg__action__DumpBasket_Result__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Result * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Result)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_Result *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_Result), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_Result__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_Result__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_Result__Sequence__fini(interfaces_pkg__action__DumpBasket_Result__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_Result__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_Result__Sequence *
interfaces_pkg__action__DumpBasket_Result__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Result__Sequence * array = (interfaces_pkg__action__DumpBasket_Result__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Result__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_Result__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_Result__Sequence__destroy(interfaces_pkg__action__DumpBasket_Result__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_Result__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_Result__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_Result__Sequence * lhs, const interfaces_pkg__action__DumpBasket_Result__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Result__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Result__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_Result__Sequence * input,
  interfaces_pkg__action__DumpBasket_Result__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Result)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_Result);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_Result * data =
      (interfaces_pkg__action__DumpBasket_Result *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_Result__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_Result__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Result__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `phase`
#include "rosidl_runtime_c/string_functions.h"

bool
interfaces_pkg__action__DumpBasket_Feedback__init(interfaces_pkg__action__DumpBasket_Feedback * msg)
{
  if (!msg) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__init(&msg->phase)) {
    interfaces_pkg__action__DumpBasket_Feedback__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_Feedback__fini(interfaces_pkg__action__DumpBasket_Feedback * msg)
{
  if (!msg) {
    return;
  }
  // phase
  rosidl_runtime_c__String__fini(&msg->phase);
}

bool
interfaces_pkg__action__DumpBasket_Feedback__are_equal(const interfaces_pkg__action__DumpBasket_Feedback * lhs, const interfaces_pkg__action__DumpBasket_Feedback * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->phase), &(rhs->phase)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Feedback__copy(
  const interfaces_pkg__action__DumpBasket_Feedback * input,
  interfaces_pkg__action__DumpBasket_Feedback * output)
{
  if (!input || !output) {
    return false;
  }
  // phase
  if (!rosidl_runtime_c__String__copy(
      &(input->phase), &(output->phase)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_Feedback *
interfaces_pkg__action__DumpBasket_Feedback__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Feedback * msg = (interfaces_pkg__action__DumpBasket_Feedback *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Feedback), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_Feedback));
  bool success = interfaces_pkg__action__DumpBasket_Feedback__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_Feedback__destroy(interfaces_pkg__action__DumpBasket_Feedback * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_Feedback__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_Feedback__Sequence__init(interfaces_pkg__action__DumpBasket_Feedback__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Feedback * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Feedback)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_Feedback *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_Feedback), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_Feedback__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_Feedback__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_Feedback__Sequence__fini(interfaces_pkg__action__DumpBasket_Feedback__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_Feedback__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_Feedback__Sequence *
interfaces_pkg__action__DumpBasket_Feedback__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_Feedback__Sequence * array = (interfaces_pkg__action__DumpBasket_Feedback__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_Feedback__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_Feedback__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_Feedback__Sequence__destroy(interfaces_pkg__action__DumpBasket_Feedback__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_Feedback__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_Feedback__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_Feedback__Sequence * lhs, const interfaces_pkg__action__DumpBasket_Feedback__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Feedback__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_Feedback__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_Feedback__Sequence * input,
  interfaces_pkg__action__DumpBasket_Feedback__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_Feedback)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_Feedback);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_Feedback * data =
      (interfaces_pkg__action__DumpBasket_Feedback *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_Feedback__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_Feedback__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_Feedback__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
#include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `goal`
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__functions.h"

bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__init(interfaces_pkg__action__DumpBasket_SendGoal_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(msg);
    return false;
  }
  // goal
  if (!interfaces_pkg__action__DumpBasket_Goal__init(&msg->goal)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(interfaces_pkg__action__DumpBasket_SendGoal_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // goal
  interfaces_pkg__action__DumpBasket_Goal__fini(&msg->goal);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Request * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // goal
  if (!interfaces_pkg__action__DumpBasket_Goal__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Request * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // goal
  if (!interfaces_pkg__action__DumpBasket_Goal__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_SendGoal_Request *
interfaces_pkg__action__DumpBasket_SendGoal_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Request * msg = (interfaces_pkg__action__DumpBasket_SendGoal_Request *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request));
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Request__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__init(interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Request * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_SendGoal_Request *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_SendGoal_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__fini(interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence *
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * array = (interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_SendGoal_Request * data =
      (interfaces_pkg__action__DumpBasket_SendGoal_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_SendGoal_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__init(interfaces_pkg__action__DumpBasket_SendGoal_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(interfaces_pkg__action__DumpBasket_SendGoal_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Response * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Response * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_SendGoal_Response *
interfaces_pkg__action__DumpBasket_SendGoal_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Response * msg = (interfaces_pkg__action__DumpBasket_SendGoal_Response *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response));
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Response__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__init(interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Response * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_SendGoal_Response *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_SendGoal_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__fini(interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence *
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * array = (interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_SendGoal_Response * data =
      (interfaces_pkg__action__DumpBasket_SendGoal_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_SendGoal_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__functions.h"

bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__init(interfaces_pkg__action__DumpBasket_SendGoal_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(msg);
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__init(&msg->request, 0)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(msg);
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__init(&msg->response, 0)) {
    interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(interfaces_pkg__action__DumpBasket_SendGoal_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__fini(&msg->request);
  // response
  interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__fini(&msg->response);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Event * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Event * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_SendGoal_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_SendGoal_Event *
interfaces_pkg__action__DumpBasket_SendGoal_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Event * msg = (interfaces_pkg__action__DumpBasket_SendGoal_Event *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event));
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Event__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__init(interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Event * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_SendGoal_Event *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_SendGoal_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__fini(interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence *
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * array = (interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__destroy(interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * lhs, const interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * input,
  interfaces_pkg__action__DumpBasket_SendGoal_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_SendGoal_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_SendGoal_Event * data =
      (interfaces_pkg__action__DumpBasket_SendGoal_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_SendGoal_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_SendGoal_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_SendGoal_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"

bool
interfaces_pkg__action__DumpBasket_GetResult_Request__init(interfaces_pkg__action__DumpBasket_GetResult_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    interfaces_pkg__action__DumpBasket_GetResult_Request__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Request__fini(interfaces_pkg__action__DumpBasket_GetResult_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Request__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Request * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Request__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Request * input,
  interfaces_pkg__action__DumpBasket_GetResult_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_GetResult_Request *
interfaces_pkg__action__DumpBasket_GetResult_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Request * msg = (interfaces_pkg__action__DumpBasket_GetResult_Request *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request));
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Request__destroy(interfaces_pkg__action__DumpBasket_GetResult_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_GetResult_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__init(interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Request * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_GetResult_Request *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_GetResult_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_GetResult_Request__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__fini(interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_GetResult_Request__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence *
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * array = (interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__destroy(interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * input,
  interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_GetResult_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_GetResult_Request * data =
      (interfaces_pkg__action__DumpBasket_GetResult_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_GetResult_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_GetResult_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `result`
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__functions.h"

bool
interfaces_pkg__action__DumpBasket_GetResult_Response__init(interfaces_pkg__action__DumpBasket_GetResult_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  // result
  if (!interfaces_pkg__action__DumpBasket_Result__init(&msg->result)) {
    interfaces_pkg__action__DumpBasket_GetResult_Response__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Response__fini(interfaces_pkg__action__DumpBasket_GetResult_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  // result
  interfaces_pkg__action__DumpBasket_Result__fini(&msg->result);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Response__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Response * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // result
  if (!interfaces_pkg__action__DumpBasket_Result__are_equal(
      &(lhs->result), &(rhs->result)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Response__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Response * input,
  interfaces_pkg__action__DumpBasket_GetResult_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  // result
  if (!interfaces_pkg__action__DumpBasket_Result__copy(
      &(input->result), &(output->result)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_GetResult_Response *
interfaces_pkg__action__DumpBasket_GetResult_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Response * msg = (interfaces_pkg__action__DumpBasket_GetResult_Response *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response));
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Response__destroy(interfaces_pkg__action__DumpBasket_GetResult_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_GetResult_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__init(interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Response * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_GetResult_Response *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_GetResult_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_GetResult_Response__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__fini(interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_GetResult_Response__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence *
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * array = (interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__destroy(interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * input,
  interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_GetResult_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_GetResult_Response * data =
      (interfaces_pkg__action__DumpBasket_GetResult_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_GetResult_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_GetResult_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
// already included above
// #include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__functions.h"

bool
interfaces_pkg__action__DumpBasket_GetResult_Event__init(interfaces_pkg__action__DumpBasket_GetResult_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    interfaces_pkg__action__DumpBasket_GetResult_Event__fini(msg);
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__init(&msg->request, 0)) {
    interfaces_pkg__action__DumpBasket_GetResult_Event__fini(msg);
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__init(&msg->response, 0)) {
    interfaces_pkg__action__DumpBasket_GetResult_Event__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Event__fini(interfaces_pkg__action__DumpBasket_GetResult_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__fini(&msg->request);
  // response
  interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__fini(&msg->response);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Event__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Event * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Event__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Event * input,
  interfaces_pkg__action__DumpBasket_GetResult_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!interfaces_pkg__action__DumpBasket_GetResult_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!interfaces_pkg__action__DumpBasket_GetResult_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_GetResult_Event *
interfaces_pkg__action__DumpBasket_GetResult_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Event * msg = (interfaces_pkg__action__DumpBasket_GetResult_Event *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event));
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Event__destroy(interfaces_pkg__action__DumpBasket_GetResult_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_GetResult_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__init(interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Event * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_GetResult_Event *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_GetResult_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_GetResult_Event__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__fini(interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_GetResult_Event__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence *
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * array = (interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__destroy(interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * lhs, const interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * input,
  interfaces_pkg__action__DumpBasket_GetResult_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_GetResult_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_GetResult_Event * data =
      (interfaces_pkg__action__DumpBasket_GetResult_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_GetResult_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_GetResult_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_GetResult_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `feedback`
// already included above
// #include "interfaces_pkg/action/detail/dump_basket__functions.h"

bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__init(interfaces_pkg__action__DumpBasket_FeedbackMessage * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(msg);
    return false;
  }
  // feedback
  if (!interfaces_pkg__action__DumpBasket_Feedback__init(&msg->feedback)) {
    interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(interfaces_pkg__action__DumpBasket_FeedbackMessage * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // feedback
  interfaces_pkg__action__DumpBasket_Feedback__fini(&msg->feedback);
}

bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__are_equal(const interfaces_pkg__action__DumpBasket_FeedbackMessage * lhs, const interfaces_pkg__action__DumpBasket_FeedbackMessage * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // feedback
  if (!interfaces_pkg__action__DumpBasket_Feedback__are_equal(
      &(lhs->feedback), &(rhs->feedback)))
  {
    return false;
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__copy(
  const interfaces_pkg__action__DumpBasket_FeedbackMessage * input,
  interfaces_pkg__action__DumpBasket_FeedbackMessage * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // feedback
  if (!interfaces_pkg__action__DumpBasket_Feedback__copy(
      &(input->feedback), &(output->feedback)))
  {
    return false;
  }
  return true;
}

interfaces_pkg__action__DumpBasket_FeedbackMessage *
interfaces_pkg__action__DumpBasket_FeedbackMessage__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_FeedbackMessage * msg = (interfaces_pkg__action__DumpBasket_FeedbackMessage *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage));
  bool success = interfaces_pkg__action__DumpBasket_FeedbackMessage__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_pkg__action__DumpBasket_FeedbackMessage__destroy(interfaces_pkg__action__DumpBasket_FeedbackMessage * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__init(interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_FeedbackMessage * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage)) {
      return false;
    }
    data = (interfaces_pkg__action__DumpBasket_FeedbackMessage *)allocator.zero_allocate(size, sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_pkg__action__DumpBasket_FeedbackMessage__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(&data[i - 1]);
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
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__fini(interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * array)
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
      interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(&array->data[i]);
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

interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence *
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * array = (interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence *)allocator.allocate(sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__destroy(interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__are_equal(const interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * lhs, const interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_FeedbackMessage__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence__copy(
  const interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * input,
  interfaces_pkg__action__DumpBasket_FeedbackMessage__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(interfaces_pkg__action__DumpBasket_FeedbackMessage);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_pkg__action__DumpBasket_FeedbackMessage * data =
      (interfaces_pkg__action__DumpBasket_FeedbackMessage *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_pkg__action__DumpBasket_FeedbackMessage__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_pkg__action__DumpBasket_FeedbackMessage__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_pkg__action__DumpBasket_FeedbackMessage__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
