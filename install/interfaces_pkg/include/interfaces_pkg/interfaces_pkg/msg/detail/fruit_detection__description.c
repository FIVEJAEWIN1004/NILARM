// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from interfaces_pkg:msg/FruitDetection.idl
// generated code does not contain a copyright notice

#include "interfaces_pkg/msg/detail/fruit_detection__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_interfaces_pkg
const rosidl_type_hash_t *
interfaces_pkg__msg__FruitDetection__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x58, 0x60, 0x9f, 0xc9, 0x1a, 0x53, 0xc1, 0x84,
      0x86, 0xe1, 0xd8, 0x86, 0x9d, 0x68, 0x6b, 0x86,
      0x8d, 0x7e, 0x2b, 0x5c, 0x53, 0xb5, 0x23, 0x0e,
      0x78, 0x58, 0x3d, 0x2d, 0x37, 0x6e, 0x92, 0x2f,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char interfaces_pkg__msg__FruitDetection__TYPE_NAME[] = "interfaces_pkg/msg/FruitDetection";

// Define type names, field names, and default values
static char interfaces_pkg__msg__FruitDetection__FIELD_NAME__x[] = "x";
static char interfaces_pkg__msg__FruitDetection__FIELD_NAME__y[] = "y";
static char interfaces_pkg__msg__FruitDetection__FIELD_NAME__z[] = "z";
static char interfaces_pkg__msg__FruitDetection__FIELD_NAME__quality[] = "quality";
static char interfaces_pkg__msg__FruitDetection__FIELD_NAME__confidence[] = "confidence";

static rosidl_runtime_c__type_description__Field interfaces_pkg__msg__FruitDetection__FIELDS[] = {
  {
    {interfaces_pkg__msg__FruitDetection__FIELD_NAME__x, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__FruitDetection__FIELD_NAME__y, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__FruitDetection__FIELD_NAME__z, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__FruitDetection__FIELD_NAME__quality, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {interfaces_pkg__msg__FruitDetection__FIELD_NAME__confidence, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
interfaces_pkg__msg__FruitDetection__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {interfaces_pkg__msg__FruitDetection__TYPE_NAME, 33, 33},
      {interfaces_pkg__msg__FruitDetection__FIELDS, 5, 5},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32 x                # \\xec\\xb9\\xb4\\xeb\\xa9\\x94\\xeb\\x9d\\xbc/\\xed\\x8c\\x94 \\xea\\xb8\\xb0\\xec\\xa4\\x80 \\xec\\x83\\x81\\xeb\\x8c\\x80\\xec\\xa2\\x8c\\xed\\x91\\x9c (m)\n"
  "float32 y\n"
  "float32 z\n"
  "string quality            # \"ripe\"(\\xec\\x9d\\xb5\\xec\\x9d\\x8c) \\xeb\\x98\\x90\\xeb\\x8a\\x94 \"bad\"(\\xeb\\xb6\\x88\\xeb\\x9f\\x89)\n"
  "float32 confidence        # \\xed\\x83\\x90\\xec\\xa7\\x80 \\xec\\x8b\\xa0\\xeb\\xa2\\xb0\\xeb\\x8f\\x84 0.0~1.0";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
interfaces_pkg__msg__FruitDetection__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {interfaces_pkg__msg__FruitDetection__TYPE_NAME, 33, 33},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 160, 160},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
interfaces_pkg__msg__FruitDetection__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *interfaces_pkg__msg__FruitDetection__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
