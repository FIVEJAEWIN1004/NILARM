// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from interfaces_pkg:msg/BasketStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "interfaces_pkg/msg/basket_status.hpp"


#ifndef INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_HPP_
#define INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__interfaces_pkg__msg__BasketStatus __attribute__((deprecated))
#else
# define DEPRECATED__interfaces_pkg__msg__BasketStatus __declspec(deprecated)
#endif

namespace interfaces_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct BasketStatus_
{
  using Type = BasketStatus_<ContainerAllocator>;

  explicit BasketStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->weight = 0l;
      this->maxweight = 0l;
      this->is_full = false;
    }
  }

  explicit BasketStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->weight = 0l;
      this->maxweight = 0l;
      this->is_full = false;
    }
  }

  // field types and members
  using _weight_type =
    int32_t;
  _weight_type weight;
  using _maxweight_type =
    int32_t;
  _maxweight_type maxweight;
  using _is_full_type =
    bool;
  _is_full_type is_full;

  // setters for named parameter idiom
  Type & set__weight(
    const int32_t & _arg)
  {
    this->weight = _arg;
    return *this;
  }
  Type & set__maxweight(
    const int32_t & _arg)
  {
    this->maxweight = _arg;
    return *this;
  }
  Type & set__is_full(
    const bool & _arg)
  {
    this->is_full = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    interfaces_pkg::msg::BasketStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const interfaces_pkg::msg::BasketStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      interfaces_pkg::msg::BasketStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      interfaces_pkg::msg::BasketStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__interfaces_pkg__msg__BasketStatus
    std::shared_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__interfaces_pkg__msg__BasketStatus
    std::shared_ptr<interfaces_pkg::msg::BasketStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BasketStatus_ & other) const
  {
    if (this->weight != other.weight) {
      return false;
    }
    if (this->maxweight != other.maxweight) {
      return false;
    }
    if (this->is_full != other.is_full) {
      return false;
    }
    return true;
  }
  bool operator!=(const BasketStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BasketStatus_

// alias to use template instance with default allocator
using BasketStatus =
  interfaces_pkg::msg::BasketStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace interfaces_pkg

#endif  // INTERFACES_PKG__MSG__DETAIL__BASKET_STATUS__STRUCT_HPP_
