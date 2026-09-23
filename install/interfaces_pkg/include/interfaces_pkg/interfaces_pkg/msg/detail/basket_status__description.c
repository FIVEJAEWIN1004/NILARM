// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

#include "interfaces_pkg/msg/detail/basket_status__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_interfaces_pkg
const rosidl_type_hash_t *
interfaces_pkg__msg__BasketStatus__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x63, 0x59, 0xec, 0x61, 0x84, 0xd1, 0x4e, 0x05,
      0xa9, 0xfa, 0x40, 0xf2, 0xf1, 0xd3, 0xbc, 0xf6,
      0x48, 0x42, 0x81, 0x04, 0xac, 0xbc, 0x37, 0x04,
      0xdd, 0x2f, 0x38, 0xfa, 0xc0, 0x61, 0xe1, 0xd8,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char interfaces_pkg__msg__BasketStatus__TYPE_NAME[] = "interfaces_pkg/msg/BasketStatus";

// Define type names, field names, and default values
static char interfaces_pkg__msg__BasketStatus__FIELD_NAME__weight[] = "weight";
static char interfaces_pkg__msg__BasketStatus__FIELD_NAME__maxweight[] = "maxweight";
static char interfaces_pkg__msg__BasketStatus__FIELD_NAME__is_full[] = "is_full";

static rosidl_runtime_c__type_description__Field interfaces_pkg__msg__BasketStatus__FIELDS[] = {
  {
    {interfaces_pkg__msg__BasketStatus__FIELD_NAME__weight, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__BasketStatus__FIELD_NAME__maxweight, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__BasketStatus__FIELD_NAME__is_full, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
interfaces_pkg__msg__BasketStatus__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {interfaces_pkg__msg__BasketStatus__TYPE_NAME, 31, 31},
      {interfaces_pkg__msg__BasketStatus__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "int32 weight             # \\xed\\x98\\x84\\xec\\x9e\\xac \\xec\\xa0\\x81\\xec\\x9e\\xac\\xeb\\x90\\x9c \\xea\\xb0\\x9c\\xec\\x88\\x98\n"
  "int32 maxweight            # \\xec\\x86\\x8c\\xed\\x98\\x95\\xeb\\xb0\\x94\\xea\\xb5\\xac\\xeb\\x8b\\x88 \\xec\\xb5\\x9c\\xeb\\x8c\\x80 \\xec\\x9a\\xa9\\xeb\\x9f\\x89\n"
  "bool is_full                # count >= capacity \\xec\\x97\\xac\\xeb\\xb6\\x80";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
interfaces_pkg__msg__BasketStatus__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {interfaces_pkg__msg__BasketStatus__TYPE_NAME, 31, 31},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 129, 129},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
interfaces_pkg__msg__BasketStatus__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *interfaces_pkg__msg__BasketStatus__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
