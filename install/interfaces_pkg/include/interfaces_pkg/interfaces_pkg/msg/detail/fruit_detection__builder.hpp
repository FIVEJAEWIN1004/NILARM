// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_pkg:msg/FruitDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/fruit_detection.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__BUILDER_HPP_
#define INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_pkg/msg/detail/fruit_detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_pkg
{

namespace msg
{

namespace builder
{

class Init_FruitDetection_confidence
{
public:
  explicit Init_FruitDetection_confidence(::interfaces_pkg::msg::FruitDetection & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::msg::FruitDetection confidence(::interfaces_pkg::msg::FruitDetection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::msg::FruitDetection msg_;
};

class Init_FruitDetection_quality
{
public:
  explicit Init_FruitDetection_quality(::interfaces_pkg::msg::FruitDetection & msg)
  : msg_(msg)
  {}
  Init_FruitDetection_confidence quality(::interfaces_pkg::msg::FruitDetection::_quality_type arg)
  {
    msg_.quality = std::move(arg);
    return Init_FruitDetection_confidence(msg_);
  }

private:
  ::interfaces_pkg::msg::FruitDetection msg_;
};

class Init_FruitDetection_z
{
public:
  explicit Init_FruitDetection_z(::interfaces_pkg::msg::FruitDetection & msg)
  : msg_(msg)
  {}
  Init_FruitDetection_quality z(::interfaces_pkg::msg::FruitDetection::_z_type arg)
  {
    msg_.z = std::move(arg);
    return Init_FruitDetection_quality(msg_);
  }

private:
  ::interfaces_pkg::msg::FruitDetection msg_;
};

class Init_FruitDetection_y
{
public:
  explicit Init_FruitDetection_y(::interfaces_pkg::msg::FruitDetection & msg)
  : msg_(msg)
  {}
  Init_FruitDetection_z y(::interfaces_pkg::msg::FruitDetection::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_FruitDetection_z(msg_);
  }

private:
  ::interfaces_pkg::msg::FruitDetection msg_;
};

class Init_FruitDetection_x
{
public:
  Init_FruitDetection_x()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FruitDetection_y x(::interfaces_pkg::msg::FruitDetection::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_FruitDetection_y(msg_);
  }

private:
  ::interfaces_pkg::msg::FruitDetection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::msg::FruitDetection>()
{
  return interfaces_pkg::msg::builder::Init_FruitDetection_x();
}

}  // namespace interfaces_pkg

#endif  // INTERFACES_PKG__MSG__DETAIL__FRUIT_DETECTION__BUILDER_HPP_
