// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/basket_status.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__TRAITS_HPP_
#define INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "interfaces_pkg/msg/detail/basket_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace interfaces_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const BasketStatus & msg,
  std::ostream & out)
{
  out << "{";
  // member: weight
  {
    out << "weight: ";
    rosidl_generator_traits::value_to_yaml(msg.weight, out);
    out << ", ";
  }

  // member: maxweight
  {
    out << "maxweight: ";
    rosidl_generator_traits::value_to_yaml(msg.maxweight, out);
    out << ", ";
  }

  // member: is_full
  {
    out << "is_full: ";
    rosidl_generator_traits::value_to_yaml(msg.is_full, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const BasketStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: weight
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "weight: ";
    rosidl_generator_traits::value_to_yaml(msg.weight, out);
    out << "\n";
  }

  // member: maxweight
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "maxweight: ";
    rosidl_generator_traits::value_to_yaml(msg.maxweight, out);
    out << "\n";
  }

  // member: is_full
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_full: ";
    rosidl_generator_traits::value_to_yaml(msg.is_full, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const BasketStatus & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace interfaces_pkg

namespace rosidl_generator_traits
{

[[deprecated("use interfaces_pkg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const interfaces_pkg::msg::BasketStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  interfaces_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use interfaces_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const interfaces_pkg::msg::BasketStatus & msg)
{
  return interfaces_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<interfaces_pkg::msg::BasketStatus>()
{
  return "interfaces_pkg::msg::BasketStatus";
}

template<>
inline const char * name<interfaces_pkg::msg::BasketStatus>()
{
  return "interfaces_pkg/msg/BasketStatus";
}

template<>
struct has_fixed_size<interfaces_pkg::msg::BasketStatus>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<interfaces_pkg::msg::BasketStatus>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<interfaces_pkg::msg::BasketStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__TRAITS_HPP_
