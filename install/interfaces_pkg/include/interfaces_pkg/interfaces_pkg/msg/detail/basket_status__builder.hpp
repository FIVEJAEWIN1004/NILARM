// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/basket_status.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__BUILDER_HPP_
#define INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_pkg/msg/detail/basket_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_pkg
{

namespace msg
{

namespace builder
{

class Init_BasketStatus_is_full
{
public:
  explicit Init_BasketStatus_is_full(::interfaces_pkg::msg::BasketStatus & msg)
  : msg_(msg)
  {}
  ::interfaces_pkg::msg::BasketStatus is_full(::interfaces_pkg::msg::BasketStatus::_is_full_type arg)
  {
    msg_.is_full = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_pkg::msg::BasketStatus msg_;
};

class Init_BasketStatus_maxweight
{
public:
  explicit Init_BasketStatus_maxweight(::interfaces_pkg::msg::BasketStatus & msg)
  : msg_(msg)
  {}
  Init_BasketStatus_is_full maxweight(::interfaces_pkg::msg::BasketStatus::_maxweight_type arg)
  {
    msg_.maxweight = std::move(arg);
    return Init_BasketStatus_is_full(msg_);
  }

private:
  ::interfaces_pkg::msg::BasketStatus msg_;
};

class Init_BasketStatus_weight
{
public:
  Init_BasketStatus_weight()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BasketStatus_maxweight weight(::interfaces_pkg::msg::BasketStatus::_weight_type arg)
  {
    msg_.weight = std::move(arg);
    return Init_BasketStatus_maxweight(msg_);
  }

private:
  ::interfaces_pkg::msg::BasketStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_pkg::msg::BasketStatus>()
{
  return interfaces_pkg::msg::builder::Init_BasketStatus_weight();
}

}  // namespace interfaces_pkg

#endif  // INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__BUILDER_HPP_
