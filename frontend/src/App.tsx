import React, { useState, useEffect } from 'react'
import type {
  FoodCategory,
  FoodDonation,
  DonationRequest,
  Pickup,
  PlatformImpact,
  User,
  DietaryType,
  QuantityUnit,
  DonationStatus,
  PickupStatus,
} from './types'
import {
  authService,
  donationService,
  pickupService,
  analyticsService,
} from './services'

export function App() {
  // Navigation & User State
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<string>('browse')
  const [loading, setLoading] = useState<boolean>(true)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Data Collections
  const [categories, setCategories] = useState<FoodCategory[]>([])
  const [donations, setDonations] = useState<FoodDonation[]>([])
  const [myDonations, setMyDonations] = useState<FoodDonation[]>([])
  const [incomingRequests, setIncomingRequests] = useState<DonationRequest[]>([])
  const [myRequests, setMyRequests] = useState<DonationRequest[]>([])
  const [availablePickups, setAvailablePickups] = useState<Pickup[]>([])
  const [myPickups, setMyPickups] = useState<Pickup[]>([])
  const [impact, setImpact] = useState<PlatformImpact | null>(null)

  // Filter States
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterDietary, setFilterDietary] = useState<string>('')
  const [filterCity, setFilterCity] = useState<string>('')

  // Admin Collections & Filter
  const [adminDonations, setAdminDonations] = useState<FoodDonation[]>([])
  const [adminPickups, setAdminPickups] = useState<Pickup[]>([])
  const [adminStatusFilter, setAdminStatusFilter] = useState<string>('')

  // Action Loading & Submission States (prevents duplicate clicks)
  const [actionLoadingId, setActionLoadingId] = useState<number | string | null>(null)
  const [isSubmittingClaim, setIsSubmittingClaim] = useState<boolean>(false)
  const [isCreatingDonation, setIsCreatingDonation] = useState<boolean>(false)
  const [claimError, setClaimError] = useState<string>('')

  // Confirmation & Details Modals
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    title: string
    message: string
    confirmText: string
    cancelText?: string
    confirmVariant?: 'danger' | 'primary'
    onConfirm: () => void | Promise<void>
  } | null>(null)
  const [confirmModalLoading, setConfirmModalLoading] = useState<boolean>(false)
  const [viewDonation, setViewDonation] = useState<FoodDonation | null>(null)

  // Modals & Active Selections
  const [selectedDonation, setSelectedDonation] = useState<FoodDonation | null>(null)
  const [showClaimModal, setShowClaimModal] = useState<boolean>(false)
  const [claimServings, setClaimServings] = useState<number>(10)
  const [claimMessage, setClaimMessage] = useState<string>('')
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false)
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false)

  // Form: Auth
  const [authEmail, setAuthEmail] = useState<string>('')
  const [authPassword, setAuthPassword] = useState<string>('')
  const [authConfirmPassword, setAuthConfirmPassword] = useState<string>('')
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false)
  const [authFirstName, setAuthFirstName] = useState<string>('')
  const [authLastName, setAuthLastName] = useState<string>('')
  const [authPhone, setAuthPhone] = useState<string>('')
  const [authRole, setAuthRole] = useState<'donor' | 'ngo_receiver' | 'volunteer'>('donor')
  const [authOrgName, setAuthOrgName] = useState<string>('')
  const [authDonorType, setAuthDonorType] = useState<string>('restaurant')
  const [authVehicleType, setAuthVehicleType] = useState<string>('two_wheeler')
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  // Modal: OTP Verification Flow
  const [showOtpModal, setShowOtpModal] = useState<boolean>(false)
  const [otpEmail, setOtpEmail] = useState<string>('')
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const [otpExpirySeconds, setOtpExpirySeconds] = useState<number>(600)
  const [resendCooldownSeconds, setResendCooldownSeconds] = useState<number>(0)
  const [otpError, setOtpError] = useState<string>('')
  const [otpSuccessMessage, setOtpSuccessMessage] = useState<string>('')
  const [isVerifyingOtp, setIsVerifyingOtp] = useState<boolean>(false)
  const [isResendingOtp, setIsResendingOtp] = useState<boolean>(false)
  const [pendingAuthSession, setPendingAuthSession] = useState<{
    tokens: { access: string; refresh: string }
    user: User
  } | null>(null)
  const otpInputRefs = React.useRef<(HTMLInputElement | null)[]>([])

  // Modal: Forgot / Reset Password Flow
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState<boolean>(false)
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState<string>('')
  const [forgotPasswordLoading, setForgotPasswordLoading] = useState<boolean>(false)
  const [forgotPasswordError, setForgotPasswordError] = useState<string>('')

  const [showResetPasswordModal, setShowResetPasswordModal] = useState<boolean>(false)
  const [resetEmail, setResetEmail] = useState<string>('')
  const [resetOtpDigits, setResetOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const [resetExpirySeconds, setResetExpirySeconds] = useState<number>(600)
  const [resetCooldownSeconds, setResetCooldownSeconds] = useState<number>(0)
  const [resetNewPassword, setResetNewPassword] = useState<string>('')
  const [resetConfirmPassword, setResetConfirmPassword] = useState<string>('')
  const [showResetNewPassword, setShowResetNewPassword] = useState<boolean>(false)
  const [showResetConfirmPassword, setShowResetConfirmPassword] = useState<boolean>(false)
  const [resetPasswordLoading, setResetPasswordLoading] = useState<boolean>(false)
  const [isResendingResetOtp, setIsResendingResetOtp] = useState<boolean>(false)
  const [resetFormErrors, setResetFormErrors] = useState<Record<string, string>>({})
  const [resetSuccessMessage, setResetSuccessMessage] = useState<string>('')
  const resetOtpInputRefs = React.useRef<(HTMLInputElement | null)[]>([])

  // Modal: Login OTP Verification Flow
  const [showLoginOtpModal, setShowLoginOtpModal] = useState<boolean>(false)
  const [loginOtpEmail, setLoginOtpEmail] = useState<string>('')
  const [loginOtpDigits, setLoginOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const [loginOtpExpirySeconds, setLoginOtpExpirySeconds] = useState<number>(600)
  const [loginOtpCooldownSeconds, setLoginOtpCooldownSeconds] = useState<number>(30)
  const [loginOtpError, setLoginOtpError] = useState<string>('')
  const [loginOtpSuccessMessage, setLoginOtpSuccessMessage] = useState<string>('')
  const [isVerifyingLoginOtp, setIsVerifyingLoginOtp] = useState<boolean>(false)
  const [isResendingLoginOtp, setIsResendingLoginOtp] = useState<boolean>(false)
  const loginOtpInputRefs = React.useRef<(HTMLInputElement | null)[]>([])

  const calculatePasswordStrength = (pw: string) => {
    if (!pw) return { score: 0, label: '', color: 'bg-gray-200', width: 'w-0' }
    let score = 0
    if (pw.length >= 8) score += 1
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score += 1
    if (/[0-9]/.test(pw)) score += 1
    if (/[^A-Za-z0-9]/.test(pw)) score += 1

    if (pw.length < 8) {
      return { score: 1, label: 'Weak', color: 'bg-rose-500', width: 'w-1/3' }
    }
    if (score <= 2) {
      return { score: 2, label: 'Medium', color: 'bg-amber-500', width: 'w-2/3' }
    }
    return { score: 3, label: 'Strong', color: 'bg-emerald-600', width: 'w-full' }
  }

  // Form: Create Donation
  const [donationForm, setDonationForm] = useState({
    title: '',
    category: 0,
    other_food_item: '',
    dietary_type: 'VEG' as DietaryType,
    quantity: 15,
    unit: 'meals' as QuantityUnit,
    servings: 15,
    expiry_hours: 8,
    pickup_address: '',
    pickup_city: 'Delhi NCR',
    pickup_contact_phone: '',
    special_instructions: '',
  })
  const [categoryFormError, setCategoryFormError] = useState<string>('')
  const [otherFoodItemError, setOtherFoodItemError] = useState<string>('')

  // Form: Admin Category Creation
  const [newCatName, setNewCatName] = useState<string>('')
  const [newCatDesc, setNewCatDesc] = useState<string>('')
  const [newCatIcon, setNewCatIcon] = useState<string>('🍲')

  // Helper: Admin check across role and staff/superuser attributes
  const isUserAdmin = (user: User | null): boolean => {
    if (!user) return false
    const role = (user.role || '').toLowerCase()
    return role === 'admin' || Boolean((user as any).is_staff) || Boolean((user as any).is_superuser)
  }

  // Helper: Determine if a donation can be cancelled according to Phase D rules
  const isDonationCancellable = (status: DonationStatus | string): boolean => {
    return ['AVAILABLE', 'REQUESTED', 'ACCEPTED', 'PICKUP_ASSIGNED'].includes(status)
  }

  // Helper: Determine if a claim request can be cancelled
  const isRequestCancellable = (status: string): boolean => {
    return status === 'PENDING'
  }

  // Helper: Tailwind styling for donation statuses (all 9 statuses)
  const getDonationStatusBadge = (status: DonationStatus | string) => {
    switch (status) {
      case 'AVAILABLE':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      case 'REQUESTED':
        return 'bg-blue-50 text-blue-700 border border-blue-200'
      case 'ACCEPTED':
        return 'bg-teal-50 text-teal-700 border border-teal-200'
      case 'PICKUP_ASSIGNED':
        return 'bg-sky-50 text-sky-700 border border-sky-200'
      case 'PICKED_UP':
        return 'bg-amber-50 text-amber-700 border border-amber-200'
      case 'DELIVERED':
        return 'bg-indigo-50 text-indigo-700 border border-indigo-200'
      case 'COMPLETED':
        return 'bg-purple-50 text-purple-700 border border-purple-200'
      case 'CANCELLED':
        return 'bg-rose-50 text-rose-700 border border-rose-200'
      case 'EXPIRED':
        return 'bg-gray-50 text-gray-600 border border-gray-200'
      default:
        return 'bg-gray-50 text-gray-700 border border-gray-200'
    }
  }

  // Helper: Tailwind styling for pickup statuses
  const getPickupStatusBadge = (status: PickupStatus | string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-gray-100 text-gray-700 border border-gray-200'
      case 'ASSIGNED':
        return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
      case 'PICKED_UP':
        return 'bg-amber-100 text-amber-800 border border-amber-200'
      case 'DELIVERED':
        return 'bg-blue-100 text-blue-800 border border-blue-200'
      case 'COMPLETED':
        return 'bg-purple-100 text-purple-800 border border-purple-200'
      case 'CANCELLED':
        return 'bg-rose-100 text-rose-800 border border-rose-200'
      default:
        return 'bg-gray-100 text-gray-800 border border-gray-200'
    }
  }

  // Helper: Tailwind styling for request statuses
  const getRequestStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-amber-100 text-amber-800 border border-amber-200'
      case 'ACCEPTED':
        return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border border-rose-200'
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-700 border border-gray-200'
      default:
        return 'bg-gray-100 text-gray-800 border border-gray-200'
    }
  }

  // Auto-clear feedback notification
  useEffect(() => {
    if (!feedback) return
    const timer = setTimeout(() => setFeedback(null), 5000)
    return () => clearTimeout(timer)
  }, [feedback])

  // OTP Countdown Timer (10 minutes)
  useEffect(() => {
    if (!showOtpModal || otpExpirySeconds <= 0) return
    const timer = setInterval(() => {
      setOtpExpirySeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [showOtpModal, otpExpirySeconds])

  // Resend OTP Cooldown Timer (30 seconds)
  useEffect(() => {
    if (resendCooldownSeconds <= 0) return
    const timer = setInterval(() => {
      setResendCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldownSeconds])

  // Reset OTP Countdown Timer (10 minutes)
  useEffect(() => {
    if (!showResetPasswordModal || resetExpirySeconds <= 0) return
    const timer = setInterval(() => {
      setResetExpirySeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [showResetPasswordModal, resetExpirySeconds])

  // Reset OTP Cooldown Timer (30 seconds)
  useEffect(() => {
    if (resetCooldownSeconds <= 0) return
    const timer = setInterval(() => {
      setResetCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [resetCooldownSeconds])

  // Login OTP Countdown Timer (10 minutes)
  useEffect(() => {
    if (!showLoginOtpModal || loginOtpExpirySeconds <= 0) return
    const timer = setInterval(() => {
      setLoginOtpExpirySeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [showLoginOtpModal, loginOtpExpirySeconds])

  // Login OTP Cooldown Timer (30 seconds)
  useEffect(() => {
    if (loginOtpCooldownSeconds <= 0) return
    const timer = setInterval(() => {
      setLoginOtpCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [loginOtpCooldownSeconds])

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Initialize Auth & App Data
  useEffect(() => {
    initAuth()
    const handleAuthLogout = () => {
      setCurrentUser(null)
      setActiveTab('browse')
      setFeedback({ type: 'error', message: 'Session expired. Please log in again.' })
    }
    window.addEventListener('foodshare_auth_logout', handleAuthLogout)
    return () => window.removeEventListener('foodshare_auth_logout', handleAuthLogout)
  }, [])

  const initAuth = async () => {
    const token = localStorage.getItem('foodshare_access_token')
    if (token) {
      try {
        const user = await authService.getCurrentUser()
        setCurrentUser(user)
        localStorage.setItem('foodshare_user', JSON.stringify(user))
      } catch {
        authService.logout()
        setCurrentUser(null)
      }
    }
    await loadInitialData()
  }

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [catsData, donationsData, impactData] = await Promise.all([
        donationService.getCategories().catch(() => []),
        donationService.getDonations().catch(() => []),
        analyticsService.getImpactMetrics().catch(() => null),
      ])
      setCategories(catsData)
      setDonations(donationsData)
      setImpact(impactData)
    } finally {
      setLoading(false)
    }
  }

  // Refetch donations via API when category, dietary, or city filter changes
  useEffect(() => {
    const params: Record<string, string | number> = {}
    if (filterCategory) params.category = filterCategory
    if (filterDietary) params.dietary_type = filterDietary
    if (filterCity) params.pickup_city = filterCity
    donationService
      .getDonations(params)
      .then((data) => setDonations(data))
      .catch(() => {})
  }, [filterCategory, filterDietary, filterCity])

  // Load Role-Specific Data when User or Tab changes
  useEffect(() => {
    if (!currentUser) return
    if (currentUser.role === 'donor') {
      loadDonorData()
    } else if (currentUser.role === 'ngo_receiver') {
      loadNgoData()
    } else if (currentUser.role === 'volunteer') {
      loadVolunteerData()
    } else if (isUserAdmin(currentUser)) {
      loadAdminData()
    }
  }, [currentUser, activeTab])

  // Refetch admin donations when adminStatusFilter changes or activeTab is admin_dashboard
  useEffect(() => {
    if (isUserAdmin(currentUser) && activeTab === 'admin_dashboard') {
      const params = adminStatusFilter ? { status: adminStatusFilter } : undefined
      donationService.getDonations(params).then(setAdminDonations).catch(() => {})
    }
  }, [adminStatusFilter, activeTab, currentUser])

  const loadDonorData = async () => {
    try {
      const donationsRes = await donationService.getMyDonations()
      setMyDonations(donationsRes)
      const reqs = donationsRes.flatMap((d) =>
        (d.requests || []).map((r) => ({
          ...r,
          donation_title: d.title,
        }))
      )
      setIncomingRequests(reqs)
    } catch {
      // Fallback
    }
  }

  const loadNgoData = async () => {
    try {
      const requestsRes = await donationService.getMyRequests()
      setMyRequests(requestsRes)
    } catch {
      // Fallback
    }
  }

  const loadVolunteerData = async () => {
    try {
      const [availRes, myPickupsRes] = await Promise.all([
        pickupService.getAvailablePickups(),
        pickupService.getMyPickups(),
      ])
      setAvailablePickups(availRes)
      setMyPickups(myPickupsRes)
    } catch {
      // Fallback
    }
  }

  const loadAdminData = async () => {
    try {
      const [catsRes, pickupsRes, impactRes, donsRes] = await Promise.all([
        donationService.getCategories(),
        pickupService.getPickups(),
        analyticsService.getImpactMetrics(),
        donationService.getDonations(adminStatusFilter ? { status: adminStatusFilter } : undefined),
      ])
      setCategories(catsRes)
      setAdminPickups(pickupsRes)
      setImpact(impactRes)
      setAdminDonations(donsRes)
    } catch {
      // Fallback
    }
  }

  // ── Actions ─────────────────────────────────────────────────────────────

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await authService.login(authEmail, authPassword)
      if (res.login_otp_required) {
        setShowAuthModal(false)
        setLoginOtpEmail(authEmail.trim())
        setLoginOtpDigits(['', '', '', '', '', ''])
        setLoginOtpExpirySeconds(600)
        setLoginOtpCooldownSeconds(30)
        setLoginOtpError('')
        setLoginOtpSuccessMessage('')
        setAuthPassword('')
        setShowLoginOtpModal(true)
        return
      }
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || ''
      const isUnverified =
        err.response?.status === 401 &&
        (typeof errorDetail === 'string' && errorDetail.toLowerCase().includes('verify your email'))

      if (isUnverified) {
        setShowAuthModal(false)
        setOtpEmail(authEmail.trim())
        setOtpDigits(['', '', '', '', '', ''])
        setOtpExpirySeconds(600)
        setResendCooldownSeconds(0)
        setOtpError('Please verify your email before continuing.')
        setOtpSuccessMessage('')
        setShowOtpModal(true)
        return
      }

      const errorMsg =
        errorDetail ||
        err.response?.data?.error ||
        'Invalid email or password. Please try again.'
      setFeedback({ type: 'error', message: errorMsg })
    }
  }

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Pre-submission client validation
    const errors: Record<string, string> = {}
    const nameRegex = /^[A-Za-z]+(?:[ '-][A-Za-z]+)*$/
    if (!authFirstName.trim()) {
      errors.first_name = 'First name is required.'
    } else if (!nameRegex.test(authFirstName.trim())) {
      errors.first_name = 'Please enter a valid first name.'
    }

    if (authLastName.trim() && !nameRegex.test(authLastName.trim())) {
      errors.last_name = 'Please enter a valid last name.'
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!authEmail.trim()) {
      errors.email = 'Email address is required.'
    } else if (!emailRegex.test(authEmail.trim())) {
      errors.email = 'Please enter a valid email address.'
    }

    if (!authPhone.trim()) {
      errors.phone_number = 'Mobile number is required.'
    } else if (!/^[0-9]{10}$/.test(authPhone.trim())) {
      errors.phone_number = 'Mobile number must contain exactly 10 digits.'
    }

    if (!authPassword) {
      errors.password = 'Password is required.'
    } else if (authPassword.length < 8) {
      errors.password = 'Password must be at least 8 characters long.'
    }

    if (!authConfirmPassword) {
      errors.confirm_password = 'Confirm password is required.'
    } else if (authPassword !== authConfirmPassword) {
      errors.confirm_password = 'Passwords do not match.'
    }

    if (authRole === 'ngo_receiver' && !authOrgName.trim()) {
      errors.organization_name = 'Organization name is required for NGOs.'
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors)
      return
    }
    setFormErrors({})

    try {
      const registeredEmail = authEmail.trim()
      const res = await authService.register({
        email: registeredEmail,
        password: authPassword,
        password_confirm: authConfirmPassword,
        first_name: authFirstName.trim(),
        last_name: authLastName.trim(),
        phone_number: authPhone.trim(),
        role: authRole,
        organization_name: authRole === 'ngo_receiver' ? authOrgName.trim() : (authOrgName.trim() || undefined),
        donor_type: authRole === 'donor' ? authDonorType : undefined,
        vehicle_type: authRole === 'volunteer' ? authVehicleType : undefined,
      })

      if (res.tokens && res.user) {
        setPendingAuthSession({ tokens: res.tokens, user: res.user })
      }
      setOtpEmail(registeredEmail)
      setOtpDigits(['', '', '', '', '', ''])
      setOtpExpirySeconds(600)
      setResendCooldownSeconds(30)
      setOtpError('')
      setOtpSuccessMessage('')

      setShowAuthModal(false)
      setAuthPassword('')
      setAuthConfirmPassword('')
      setFormErrors({})
      setShowOtpModal(true)
    } catch (err: any) {
      const errData = err.response?.data
      const newErrors: Record<string, string> = {}
      let genericError = ''

      if (errData && typeof errData === 'object') {
        if (errData.phone_number) {
          newErrors.phone_number = Array.isArray(errData.phone_number) ? errData.phone_number[0] : String(errData.phone_number)
        }
        if (errData.email) {
          newErrors.email = Array.isArray(errData.email) ? errData.email[0] : String(errData.email)
        }
        if (errData.first_name) {
          newErrors.first_name = Array.isArray(errData.first_name) ? errData.first_name[0] : String(errData.first_name)
        }
        if (errData.last_name) {
          newErrors.last_name = Array.isArray(errData.last_name) ? errData.last_name[0] : String(errData.last_name)
        }
        if (errData.password) {
          newErrors.password = Array.isArray(errData.password) ? errData.password[0] : String(errData.password)
        }
        if (errData.password_confirm) {
          newErrors.confirm_password = Array.isArray(errData.password_confirm) ? errData.password_confirm[0] : String(errData.password_confirm)
        }
        if (errData.organization_name) {
          newErrors.organization_name = Array.isArray(errData.organization_name) ? errData.organization_name[0] : String(errData.organization_name)
        }
        if (errData.error) {
          const errMsg = String(errData.error)
          if (errMsg.toLowerCase().includes('phone') || errMsg.toLowerCase().includes('mobile')) {
            newErrors.phone_number = errMsg
          } else if (errMsg.toLowerCase().includes('email')) {
            newErrors.email = errMsg
          } else if (errMsg.toLowerCase().includes('password')) {
            newErrors.confirm_password = errMsg
          } else {
            genericError = errMsg
          }
        }
        if (errData.non_field_errors) {
          genericError = Array.isArray(errData.non_field_errors) ? errData.non_field_errors[0] : String(errData.non_field_errors)
        }
        if (errData.detail) {
          genericError = String(errData.detail)
        }
      } else {
        genericError = 'Registration failed. Please check your network and try again.'
      }

      if (Object.keys(newErrors).length > 0) {
        setFormErrors(newErrors)
      }
      if (genericError) {
        setFeedback({ type: 'error', message: genericError })
      }
    }
  }

  const handleOtpDigitChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...otpDigits]
    newDigits[index] = char
    setOtpDigits(newDigits)
    setOtpError('')

    if (char && index < 5) {
      otpInputRefs.current[index + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (!pasted) return
    const newDigits = [...otpDigits]
    for (let i = 0; i < pasted.length; i++) {
      newDigits[i] = pasted[i]
    }
    setOtpDigits(newDigits)
    setOtpError('')
    const nextFocusIndex = Math.min(pasted.length, 5)
    otpInputRefs.current[nextFocusIndex]?.focus()
  }

  const handleVerifyOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const code = otpDigits.join('')
    if (code.length !== 6) {
      setOtpError('Please enter all 6 digits of the verification code.')
      return
    }
    if (otpExpirySeconds <= 0) {
      setOtpError('Verification code has expired. Please click Resend OTP to get a new code.')
      return
    }

    setIsVerifyingOtp(true)
    setOtpError('')
    try {
      const res = await authService.verifyOtp(otpEmail, code)
      setOtpSuccessMessage(res.message || 'Email verified successfully.')

      const sessionTokens = res.tokens || pendingAuthSession?.tokens
      const sessionUser = res.user || pendingAuthSession?.user

      if (sessionTokens && sessionUser) {
        authService.setSession(sessionTokens, sessionUser)
        setCurrentUser(sessionUser)
        setTimeout(() => {
          setShowOtpModal(false)
          setOtpSuccessMessage('')
          setPendingAuthSession(null)
          setFeedback({
            type: 'success',
            message: `Welcome to FoodShare, ${sessionUser.first_name || sessionUser.email}! Email verified.`,
          })
          if (sessionUser.role === 'donor') setActiveTab('donor_dashboard')
          else if (sessionUser.role === 'ngo_receiver') setActiveTab('ngo_dashboard')
          else if (sessionUser.role === 'volunteer') setActiveTab('volunteer_dashboard')
          else if (sessionUser.role === 'admin') setActiveTab('admin_dashboard')
        }, 1200)
      } else {
        setTimeout(() => {
          setShowOtpModal(false)
          setOtpSuccessMessage('')
          setShowAuthModal(true)
          setIsRegisterMode(false)
          setFeedback({
            type: 'success',
            message: 'Email verified successfully! Please sign in with your credentials.',
          })
        }, 1200)
      }
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.response?.data?.otp?.[0] ||
        'Invalid verification code. Please try again.'
      setOtpError(errorMsg)
    } finally {
      setIsVerifyingOtp(false)
    }
  }

  const handleResendOtpSubmit = async () => {
    if (isResendingOtp || resendCooldownSeconds > 0) return
    setIsResendingOtp(true)
    setOtpError('')
    try {
      const res = await authService.resendOtp(otpEmail)
      setResendCooldownSeconds(30)
      setOtpDigits(['', '', '', '', '', ''])
      setOtpExpirySeconds(600)
      setFeedback({
        type: 'success',
        message: res.message || 'New verification code sent. Check your backend console terminal.',
      })
      otpInputRefs.current[0]?.focus()
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to resend code. Please wait a moment and try again.'
      setOtpError(errorMsg)
    } finally {
      setIsResendingOtp(false)
    }
  }

  // ── Login OTP Action Handlers ──────────────────────────────────────────
  const handleLoginOtpDigitChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...loginOtpDigits]
    newDigits[index] = char
    setLoginOtpDigits(newDigits)
    setLoginOtpError('')

    if (char && index < 5) {
      loginOtpInputRefs.current[index + 1]?.focus()
    }
  }

  const handleLoginOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !loginOtpDigits[index] && index > 0) {
      loginOtpInputRefs.current[index - 1]?.focus()
    }
  }

  const handleLoginOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (!pasted) return
    const newDigits = [...loginOtpDigits]
    for (let i = 0; i < pasted.length; i++) {
      newDigits[i] = pasted[i]
    }
    setLoginOtpDigits(newDigits)
    setLoginOtpError('')
    const nextFocusIndex = Math.min(pasted.length, 5)
    loginOtpInputRefs.current[nextFocusIndex]?.focus()
  }

  const handleVerifyLoginOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const code = loginOtpDigits.join('')
    if (code.length !== 6) {
      setLoginOtpError('Please enter all 6 digits of the login verification code.')
      return
    }
    if (loginOtpExpirySeconds <= 0) {
      setLoginOtpError('Login verification code has expired. Please click Resend Code to request a new one.')
      return
    }

    setIsVerifyingLoginOtp(true)
    setLoginOtpError('')
    try {
      const res = await authService.verifyLoginOtp(loginOtpEmail, code)
      const user = res.user
      setLoginOtpSuccessMessage(res.message || 'Login successful.')
      if (user) {
        setCurrentUser(user)
        setTimeout(() => {
          setShowLoginOtpModal(false)
          setLoginOtpSuccessMessage('')
          setFeedback({
            type: 'success',
            message: `Welcome back, ${user.first_name || user.email}!`,
          })
          if (user.role === 'donor') setActiveTab('donor_dashboard')
          else if (user.role === 'ngo_receiver') setActiveTab('ngo_dashboard')
          else if (user.role === 'volunteer') setActiveTab('volunteer_dashboard')
          else if (user.role === 'admin') setActiveTab('admin_dashboard')
        }, 1000)
      }
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.response?.data?.otp?.[0] ||
        'Invalid verification code. Please try again.'
      setLoginOtpError(errorMsg)
    } finally {
      setIsVerifyingLoginOtp(false)
    }
  }

  const handleResendLoginOtpSubmit = async () => {
    if (isResendingLoginOtp || loginOtpCooldownSeconds > 0) return
    setIsResendingLoginOtp(true)
    setLoginOtpError('')
    try {
      const res = await authService.resendLoginOtp(loginOtpEmail)
      setLoginOtpCooldownSeconds(30)
      setLoginOtpDigits(['', '', '', '', '', ''])
      setLoginOtpExpirySeconds(600)
      setFeedback({
        type: 'success',
        message: res.message || 'New login verification code sent. Check your backend console terminal.',
      })
      loginOtpInputRefs.current[0]?.focus()
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to resend code. Please wait a moment and try again.'
      setLoginOtpError(errorMsg)
    } finally {
      setIsResendingLoginOtp(false)
    }
  }

  // ── Password Reset Action Handlers ─────────────────────────────────────
  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const email = forgotPasswordEmail.trim().toLowerCase()
    if (!email) {
      setForgotPasswordError('Email address is required.')
      return
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setForgotPasswordError('Please enter a valid email address.')
      return
    }

    setForgotPasswordLoading(true)
    setForgotPasswordError('')
    try {
      await authService.requestPasswordReset(email)
      setShowForgotPasswordModal(false)
      setResetEmail(email)
      setResetOtpDigits(['', '', '', '', '', ''])
      setResetExpirySeconds(600)
      setResetCooldownSeconds(30)
      setResetNewPassword('')
      setResetConfirmPassword('')
      setResetFormErrors({})
      setResetSuccessMessage('')
      setShowResetPasswordModal(true)
      setFeedback({
        type: 'success',
        message: 'Password reset code sent. Please check your email.',
      })
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.email?.[0] ||
        'Failed to send reset code. Please try again.'
      setForgotPasswordError(errorMsg)
    } finally {
      setForgotPasswordLoading(false)
    }
  }

  const handleResetOtpDigitChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...resetOtpDigits]
    newDigits[index] = char
    setResetOtpDigits(newDigits)
    if (resetFormErrors.otp) {
      setResetFormErrors((prev) => ({ ...prev, otp: '' }))
    }

    if (char && index < 5) {
      resetOtpInputRefs.current[index + 1]?.focus()
    }
  }

  const handleResetOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !resetOtpDigits[index] && index > 0) {
      resetOtpInputRefs.current[index - 1]?.focus()
    }
  }

  const handleResetOtpPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (!pasted) return
    const newDigits = [...resetOtpDigits]
    for (let i = 0; i < pasted.length; i++) {
      newDigits[i] = pasted[i]
    }
    setResetOtpDigits(newDigits)
    if (resetFormErrors.otp) {
      setResetFormErrors((prev) => ({ ...prev, otp: '' }))
    }
    const nextFocusIndex = Math.min(pasted.length, 5)
    resetOtpInputRefs.current[nextFocusIndex]?.focus()
  }

  const handleResetPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const code = resetOtpDigits.join('')
    const errors: Record<string, string> = {}

    if (code.length !== 6) {
      errors.otp = 'Please enter all 6 digits of the verification code.'
    }
    if (resetExpirySeconds <= 0) {
      errors.otp = 'Verification code has expired. Please request a new code.'
    }
    if (!resetNewPassword) {
      errors.new_password = 'New password is required.'
    } else if (resetNewPassword.length < 8) {
      errors.new_password = 'Password must be at least 8 characters long.'
    }
    if (!resetConfirmPassword) {
      errors.confirm_password = 'Confirm password is required.'
    } else if (resetNewPassword !== resetConfirmPassword) {
      errors.confirm_password = 'Passwords do not match.'
    }

    if (Object.keys(errors).length > 0) {
      setResetFormErrors(errors)
      return
    }
    setResetFormErrors({})

    setResetPasswordLoading(true)
    try {
      const res = await authService.confirmPasswordReset({
        email: resetEmail,
        otp: code,
        new_password: resetNewPassword,
        new_password_confirm: resetConfirmPassword,
      })
      setResetSuccessMessage(res.message || 'Password reset successfully.')
      setTimeout(() => {
        setShowResetPasswordModal(false)
        setResetSuccessMessage('')
        setAuthEmail(resetEmail)
        setAuthPassword('')
        setIsRegisterMode(false)
        setShowAuthModal(true)
        setFeedback({
          type: 'success',
          message: 'Password reset successfully! Please sign in with your new password.',
        })
      }, 1500)
    } catch (err: any) {
      const errData = err.response?.data
      const newErrors: Record<string, string> = {}
      let genericErr = ''

      if (errData && typeof errData === 'object') {
        if (errData.field_errors) {
          if (errData.field_errors.new_password_confirm) {
            newErrors.confirm_password = Array.isArray(errData.field_errors.new_password_confirm)
              ? errData.field_errors.new_password_confirm[0]
              : String(errData.field_errors.new_password_confirm)
          }
          if (errData.field_errors.new_password) {
            newErrors.new_password = Array.isArray(errData.field_errors.new_password)
              ? errData.field_errors.new_password[0]
              : String(errData.field_errors.new_password)
          }
          if (errData.field_errors.otp) {
            newErrors.otp = Array.isArray(errData.field_errors.otp)
              ? errData.field_errors.otp[0]
              : String(errData.field_errors.otp)
          }
        }
        if (errData.error) {
          const errMsg = String(errData.error)
          if (errMsg.toLowerCase().includes('password') && (errMsg.toLowerCase().includes('match') || errMsg.toLowerCase().includes('confirm'))) {
            newErrors.confirm_password = errMsg
          } else if (
            errMsg.toLowerCase().includes('code') ||
            errMsg.toLowerCase().includes('otp') ||
            errMsg.toLowerCase().includes('attempt') ||
            errMsg.toLowerCase().includes('expired')
          ) {
            newErrors.otp = errMsg
          } else {
            genericErr = errMsg
          }
        }
      } else {
        genericErr = 'Failed to reset password. Please try again.'
      }

      if (Object.keys(newErrors).length > 0) {
        setResetFormErrors(newErrors)
      }
      if (genericErr) {
        setResetFormErrors((prev) => ({ ...prev, general: genericErr }))
      }
    } finally {
      setResetPasswordLoading(false)
    }
  }

  const handleResendResetOtp = async () => {
    if (isResendingResetOtp || resetCooldownSeconds > 0) return
    setIsResendingResetOtp(true)
    setResetFormErrors({})
    try {
      await authService.resendPasswordReset(resetEmail)
      setResetCooldownSeconds(30)
      setResetOtpDigits(['', '', '', '', '', ''])
      setResetExpirySeconds(600)
      setFeedback({
        type: 'success',
        message: 'A fresh password reset code has been sent to your email.',
      })
      resetOtpInputRefs.current[0]?.focus()
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to resend code. Please try again.'
      setResetFormErrors((prev) => ({ ...prev, otp: errorMsg }))
    } finally {
      setIsResendingResetOtp(false)
    }
  }

  const handleLogout = () => {
    authService.logout()
    setCurrentUser(null)
    setActiveTab('browse')
    setFeedback({ type: 'success', message: 'Logged out successfully.' })
  }

  const handleCreateDonation = async (e: React.FormEvent) => {
    e.preventDefault()
    setCategoryFormError('')
    setOtherFoodItemError('')

    if (!donationForm.category) {
      setCategoryFormError('Please select a food category.')
      setFeedback({ type: 'error', message: 'Please select a food category.' })
      return
    }

    const selectedCat = categories.find((c) => c.id === donationForm.category)
    const isOther = selectedCat?.slug === 'other' || selectedCat?.name.toLowerCase() === 'other'

    if (isOther) {
      const trimmedItem = (donationForm.other_food_item || '').trim()
      if (!trimmedItem) {
        setOtherFoodItemError('Please specify the food item when selecting "Other".')
        setFeedback({ type: 'error', message: 'Please specify the food item when selecting "Other".' })
        return
      }
      if (trimmedItem.length > 100) {
        setOtherFoodItemError('Food item description cannot exceed 100 characters.')
        setFeedback({ type: 'error', message: 'Food item description cannot exceed 100 characters.' })
        return
      }
    }

    if (donationForm.quantity <= 0) {
      setFeedback({ type: 'error', message: 'Quantity must be strictly greater than 0.' })
      return
    }

    if (donationForm.servings < 1) {
      setFeedback({ type: 'error', message: 'Servings must be at least 1 portion.' })
      return
    }

    if (!/^[0-9]{10}$/.test(donationForm.pickup_contact_phone.trim())) {
      setFeedback({ type: 'error', message: 'Contact phone must contain exactly 10 digits.' })
      return
    }

    if (!donationForm.pickup_address.trim()) {
      setFeedback({ type: 'error', message: 'Pickup address is required.' })
      return
    }

    const expiryDate = new Date(Date.now() + donationForm.expiry_hours * 3600 * 1000).toISOString()
    setIsCreatingDonation(true)
    try {
      await donationService.createDonation({
        title: donationForm.title.trim(),
        category: donationForm.category,
        other_food_item: isOther ? donationForm.other_food_item.trim() : null,
        dietary_type: donationForm.dietary_type,
        quantity: donationForm.quantity,
        unit: donationForm.unit,
        servings: donationForm.servings,
        expiry_at: expiryDate,
        pickup_address: donationForm.pickup_address.trim(),
        pickup_city: donationForm.pickup_city.trim(),
        pickup_contact_phone: donationForm.pickup_contact_phone.trim(),
        special_instructions: donationForm.special_instructions.trim(),
      })
      setFeedback({ type: 'success', message: 'Food donation published successfully!' })
      setDonationForm((prev) => ({
        ...prev,
        title: '',
        category: 0,
        other_food_item: '',
        pickup_address: '',
        special_instructions: '',
      }))
      setCategoryFormError('')
      setOtherFoodItemError('')
      await loadDonorData()
      if (isUserAdmin(currentUser)) await loadAdminData()
      await loadInitialData()
      setActiveTab('donor_dashboard')
    } catch (err: any) {
      const msg =
        err.response?.data?.other_food_item?.[0] ||
        err.response?.data?.category?.[0] ||
        err.response?.data?.error ||
        err.response?.data?.expiry_at?.[0] ||
        err.response?.data?.quantity?.[0] ||
        err.response?.data?.servings?.[0] ||
        'Failed to publish donation.'
      setFeedback({ type: 'error', message: msg })
    } finally {
      setIsCreatingDonation(false)
    }
  }

  const handleClaimSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDonation) return
    setClaimError('')

    if (claimServings <= 0 || claimServings > selectedDonation.servings) {
      const err = `Requested servings must be between 1 and ${selectedDonation.servings}.`
      setClaimError(err)
      return
    }

    if (!claimMessage.trim()) {
      setClaimError('Please provide a message or distribution purpose.')
      return
    }

    setIsSubmittingClaim(true)
    try {
      await donationService.requestDonation(selectedDonation.id, claimServings, claimMessage.trim())
      setFeedback({ type: 'success', message: `Claim request submitted for "${selectedDonation.title}"!` })
      setShowClaimModal(false)
      setClaimMessage('')
      setClaimError('')
      await loadNgoData()
      await loadInitialData()
    } catch (err: any) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.requested_servings?.[0] ||
        err.response?.data?.donation?.[0] ||
        err.response?.data?.detail ||
        'Failed to submit claim request.'
      setClaimError(msg)
      setFeedback({ type: 'error', message: msg })
    } finally {
      setIsSubmittingClaim(false)
    }
  }

  const handleAcceptRequest = (requestId: number, donationTitle?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Accept Claim Request',
      message: `Are you sure you want to accept this claim request for "${donationTitle || 'this donation'}"? A volunteer pickup task will be generated, and any competing requests for this donation will be automatically rejected.`,
      confirmText: 'Accept Request',
      confirmVariant: 'primary',
      onConfirm: async () => {
        setActionLoadingId(requestId)
        try {
          await donationService.acceptRequest(requestId)
          setFeedback({ type: 'success', message: 'Claim request accepted! A pickup task has been generated.' })
          await loadDonorData()
          if (isUserAdmin(currentUser)) await loadAdminData()
          await loadInitialData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to accept claim request.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleRejectRequest = (requestId: number) => {
    setConfirmModal({
      isOpen: true,
      title: 'Reject Claim Request',
      message: 'Are you sure you want to reject this claim request? If no other pending requests exist, the donation will remain available for other shelters.',
      confirmText: 'Reject Request',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setActionLoadingId(requestId)
        try {
          await donationService.rejectRequest(requestId)
          setFeedback({ type: 'success', message: 'Request rejected.' })
          await loadDonorData()
          if (isUserAdmin(currentUser)) await loadAdminData()
          await loadInitialData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to reject request.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleCancelDonation = (donationId: number, donationTitle?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Cancel Food Donation',
      message: `Are you sure you want to cancel "${donationTitle || 'this donation'}"? Any pending NGO claim requests and associated pickups will also be cancelled.`,
      confirmText: 'Yes, Cancel Donation',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setActionLoadingId(donationId)
        try {
          await donationService.cancelDonation(donationId)
          setFeedback({ type: 'success', message: 'Donation has been cancelled.' })
          await loadDonorData()
          if (isUserAdmin(currentUser)) await loadAdminData()
          await loadInitialData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to cancel donation.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleCancelRequest = (requestId: number, donationTitle?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Cancel Claim Request',
      message: `Are you sure you want to cancel your claim request for "${donationTitle || 'this donation'}"?`,
      confirmText: 'Yes, Cancel Request',
      confirmVariant: 'danger',
      onConfirm: async () => {
        setActionLoadingId(requestId)
        try {
          await donationService.cancelRequest(requestId)
          setFeedback({ type: 'success', message: 'Claim request has been cancelled.' })
          await loadNgoData()
          await loadInitialData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to cancel claim request.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleClaimPickup = async (pickupId: number) => {
    setActionLoadingId(pickupId)
    try {
      await pickupService.claimPickup(pickupId)
      setFeedback({ type: 'success', message: 'Pickup task assigned to you successfully!' })
      await loadVolunteerData()
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Failed to claim pickup. It may have already been assigned.'
      setFeedback({ type: 'error', message: msg })
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleMarkPickedUp = (pickupId: number, title?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Confirm Food Pickup',
      message: `Confirm that you have arrived and collected "${title || 'the food'}" from the donor location?`,
      confirmText: 'Mark Picked Up',
      confirmVariant: 'primary',
      onConfirm: async () => {
        setActionLoadingId(pickupId)
        try {
          await pickupService.markPickedUp(pickupId)
          setFeedback({ type: 'success', message: 'Pickup marked as PICKED UP.' })
          await loadVolunteerData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to update pickup status.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleMarkDelivered = (pickupId: number, title?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Confirm Food Delivery',
      message: `Confirm that you have safely transported and delivered "${title || 'the food'}" to the recipient shelter/NGO?`,
      confirmText: 'Mark Delivered',
      confirmVariant: 'primary',
      onConfirm: async () => {
        setActionLoadingId(pickupId)
        try {
          await pickupService.markDelivered(pickupId)
          setFeedback({ type: 'success', message: 'Pickup marked as DELIVERED to NGO.' })
          await loadVolunteerData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to update delivery status.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleMarkCompleted = (pickupId: number, title?: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Verify & Complete Delivery',
      message: `Confirm that the distribution of "${title || 'this delivery'}" is fully completed and verified?`,
      confirmText: 'Verify & Complete Task',
      confirmVariant: 'primary',
      onConfirm: async () => {
        setActionLoadingId(pickupId)
        try {
          await pickupService.markCompleted(pickupId)
          setFeedback({ type: 'success', message: 'Pickup marked as COMPLETED. Delivery verified!' })
          await loadVolunteerData()
          await loadInitialData()
        } catch (err: any) {
          const msg = err.response?.data?.error || 'Failed to complete pickup.'
          setFeedback({ type: 'error', message: msg })
        } finally {
          setActionLoadingId(null)
          setConfirmModal(null)
        }
      },
    })
  }

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const cat = await donationService.createCategory({
        name: newCatName,
        description: newCatDesc,
        icon: newCatIcon,
        is_active: true,
      })
      setFeedback({ type: 'success', message: `Category "${cat.name}" created successfully!` })
      setNewCatName('')
      setNewCatDesc('')
      const updatedCats = await donationService.getCategories()
      setCategories(updatedCats)
    } catch (err: any) {
      const msg = err.response?.data?.name?.[0] || 'Failed to create category.'
      setFeedback({ type: 'error', message: msg })
    }
  }

  const handleToggleCategoryActive = async (cat: FoodCategory) => {
    try {
      await donationService.updateCategory(cat.id, { is_active: !cat.is_active })
      setFeedback({ type: 'success', message: `Category "${cat.name}" status updated.` })
      const updatedCats = await donationService.getCategories()
      setCategories(updatedCats)
    } catch (err: any) {
      setFeedback({ type: 'error', message: 'Failed to update category.' })
    }
  }

  // Filtered available donations
  const filteredDonations = donations.filter((item) => {
    if (filterCategory && item.category !== Number(filterCategory)) return false
    if (filterDietary && item.dietary_type !== filterDietary) return false
    if (filterCity && !item.pickup_city.toLowerCase().includes(filterCity.toLowerCase())) return false
    return true
  })

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-800">
      {/* ── Top Alert Banner ───────────────────────────────────────────────── */}
      <header className="bg-emerald-800 text-white text-xs py-2 px-4 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <span className="bg-emerald-700 px-2 py-0.5 rounded font-bold uppercase tracking-wide">FoodShare</span>
          <span>Community Food Surplus Rescue Platform • Zero Food Waste Mission</span>
        </div>
        <div className="flex items-center space-x-4">
          {currentUser ? (
            <span className="font-medium">
              Role: <strong className="uppercase">{currentUser.role}</strong> ({currentUser.email})
            </span>
          ) : (
            <span className="text-emerald-200">Browsing as Guest</span>
          )}
        </div>
      </header>

      {/* ── Primary Navigation ────────────────────────────────────────────── */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('browse')}>
            <span className="text-3xl">🍲</span>
            <div>
              <h1 className="text-2xl font-bold text-emerald-800 leading-tight">FoodShare</h1>
              <p className="text-xs text-gray-500 font-medium">Surplus Donation &amp; Relief Logistics</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
            <button
              onClick={() => setActiveTab('browse')}
              className={`px-3 py-2 rounded-lg transition ${
                activeTab === 'browse' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Available Food
            </button>
            <button
              onClick={() => setActiveTab('categories')}
              className={`px-3 py-2 rounded-lg transition ${
                activeTab === 'categories' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Categories
            </button>

            {currentUser?.role === 'donor' && (
              <>
                <button
                  onClick={() => setActiveTab('donor_dashboard')}
                  className={`px-3 py-2 rounded-lg transition ${
                    activeTab === 'donor_dashboard' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  My Donations &amp; Requests
                </button>
                <button
                  onClick={() => setActiveTab('donor_create')}
                  className={`px-3 py-2 rounded-lg transition ${
                    activeTab === 'donor_create' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  + Post Donation
                </button>
              </>
            )}

            {currentUser?.role === 'ngo_receiver' && (
              <button
                onClick={() => setActiveTab('ngo_dashboard')}
                className={`px-3 py-2 rounded-lg transition ${
                  activeTab === 'ngo_dashboard' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                NGO Claims Hub
              </button>
            )}

            {currentUser?.role === 'volunteer' && (
              <button
                onClick={() => setActiveTab('volunteer_dashboard')}
                className={`px-3 py-2 rounded-lg transition ${
                  activeTab === 'volunteer_dashboard' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Volunteer Deliveries
              </button>
            )}

            {isUserAdmin(currentUser) && (
              <button
                onClick={() => setActiveTab('admin_dashboard')}
                className={`px-3 py-2 rounded-lg transition ${
                  activeTab === 'admin_dashboard' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Admin Management
              </button>
            )}

            <button
              onClick={() => setActiveTab('impact')}
              className={`px-3 py-2 rounded-lg transition ${
                activeTab === 'impact' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Impact Stats
            </button>

            {currentUser ? (
              <button
                onClick={handleLogout}
                className="ml-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-xs font-semibold"
              >
                Sign Out
              </button>
            ) : (
              <button
                onClick={() => {
                  setIsRegisterMode(false)
                  setShowAuthModal(true)
                }}
                className="ml-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
              >
                Sign In / Register
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* ── Notification Feedback Toast ────────────────────────────────────── */}
      {feedback && (
        <div
          className={`max-w-7xl mx-auto w-full mt-4 px-4 py-3 rounded-lg text-sm flex justify-between items-center border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          <span>{feedback.type === 'success' ? '✓' : '⚠️'} {feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="font-bold hover:opacity-75">
            ✕
          </button>
        </div>
      )}

      {/* ── Main Workspace Content ─────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        {/* VIEW 1: BROWSE AVAILABLE FOOD SURPLUS */}
        {activeTab === 'browse' && (
          <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Available Surplus Food</h2>
                <p className="text-sm text-gray-500">
                  Verified edible food posted by restaurants, hotels, and community donors ready for distribution.
                </p>
              </div>
              {currentUser?.role === 'donor' && (
                <button
                  onClick={() => setActiveTab('donor_create')}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition"
                >
                  + Post New Donation
                </button>
              )}
            </div>

            {/* Category Quick Filter Ribbon */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Browse by Food Category
                </span>
                {filterCategory && (
                  <button
                    onClick={() => setFilterCategory('')}
                    className="text-xs text-emerald-600 hover:text-emerald-800 font-semibold underline"
                  >
                    Reset category
                  </button>
                )}
              </div>
              <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
                <button
                  onClick={() => setFilterCategory('')}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition ${
                    filterCategory === ''
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  All Food Items
                </button>
                {categories
                  .filter((c) => c.is_active !== false)
                  .map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => setFilterCategory(String(cat.id))}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 ${
                        filterCategory === String(cat.id)
                          ? 'bg-emerald-600 text-white shadow-sm ring-2 ring-emerald-300'
                          : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <span>{cat.icon || '🏷️'}</span>
                      <span>{cat.name}</span>
                    </button>
                  ))}
              </div>
            </div>

            {/* Filter Controls */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Category</label>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2 focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">All Categories</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon ? `${cat.icon} ` : ''}{cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex-1 min-w-[150px]">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Dietary Type</label>
                <select
                  value={filterDietary}
                  onChange={(e) => setFilterDietary(e.target.value)}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2 focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">All Dietary Types</option>
                  <option value="VEG">Vegetarian (Veg)</option>
                  <option value="NON_VEG">Non-Vegetarian</option>
                  <option value="VEGAN">Vegan</option>
                  <option value="EGG">Contains Egg</option>
                </select>
              </div>

              <div className="flex-1 min-w-[180px]">
                <label className="block text-xs font-semibold text-gray-600 mb-1">City / Region</label>
                <input
                  type="text"
                  placeholder="e.g. Delhi, Mumbai, Noida"
                  value={filterCity}
                  onChange={(e) => setFilterCity(e.target.value)}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2 focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              {(filterCategory || filterDietary || filterCity) && (
                <div className="self-end">
                  <button
                    onClick={() => {
                      setFilterCategory('')
                      setFilterDietary('')
                      setFilterCity('')
                    }}
                    className="text-xs text-gray-500 hover:text-gray-800 underline pb-2"
                  >
                    Reset Filters
                  </button>
                </div>
              )}
            </div>

            {loading ? (
              <div className="p-16 text-center text-gray-400">Loading surplus listings...</div>
            ) : filteredDonations.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                <span className="text-4xl mb-3 block">🥗</span>
                <h3 className="text-lg font-semibold text-gray-800">No matching surplus donations found</h3>
                <p className="text-sm text-gray-500 max-w-md mx-auto mt-1">
                  Try adjusting your filters or check back shortly as restaurants publish surplus meals.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredDonations.map((item) => (
                  <div key={item.id} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-bold px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 flex items-center gap-1">
                          {item.category_details?.slug === 'other' || item.category_details?.name?.toLowerCase() === 'other'
                            ? (item.other_food_item ? `📦 Other • ${item.other_food_item}` : '📦 Other')
                            : `${item.category_details?.icon ? `${item.category_details.icon} ` : ''}${item.category_details?.name || 'Cooked Food'}`}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
                          {item.dietary_type}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-gray-900 mb-1">{item.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-2 mb-3">{item.description || 'Surplus portion available for community distribution.'}</p>
                      
                      <div className="space-y-1 text-xs text-gray-600 mb-4 bg-gray-50 p-3 rounded-lg border border-gray-100">
                        <div>
                          <strong>Quantity:</strong> {item.quantity} {item.unit} (~{item.servings} portions)
                        </div>
                        <div>
                          <strong>Pickup Location:</strong> {item.pickup_city} — {item.pickup_address}
                        </div>
                        <div className="text-red-700 font-medium">
                          <strong>Expires:</strong> {new Date(item.expiry_at).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-gray-100 flex justify-between items-center gap-2">
                      <div className="flex items-center gap-2">
                        {getDonationStatusBadge(item.status)}
                        <button
                          type="button"
                          onClick={() => setViewDonation(item)}
                          className="text-xs text-emerald-700 hover:text-emerald-900 font-medium underline"
                        >
                          Details
                        </button>
                      </div>
                      {currentUser?.role === 'ngo_receiver' ? (
                        <button
                          onClick={() => {
                            setSelectedDonation(item)
                            setClaimServings(item.servings)
                            setClaimError('')
                            setShowClaimModal(true)
                          }}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                        >
                          Claim Food
                        </button>
                      ) : !currentUser ? (
                        <button
                          onClick={() => {
                            setIsRegisterMode(false)
                            setShowAuthModal(true)
                          }}
                          className="text-emerald-700 hover:text-emerald-800 text-xs font-semibold underline"
                        >
                          Sign In to Claim
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* VIEW: FOOD CATEGORIES DIRECTORY */}
        {activeTab === 'categories' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <span>🏷️</span> Food Categories Directory
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Explore surplus food classifications accepted and distributed across the FoodShare network.
                  </p>
                </div>
                {currentUser?.role === 'donor' && (
                  <button
                    onClick={() => setActiveTab('donor_create')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition"
                  >
                    + Post Donation
                  </button>
                )}
              </div>
            </div>

            {loading ? (
              <div className="p-16 text-center text-gray-400">Loading categories...</div>
            ) : categories.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                <span className="text-4xl mb-3 block">📦</span>
                <h3 className="text-lg font-semibold text-gray-800">No categories found</h3>
                <p className="text-sm text-gray-500 max-w-md mx-auto mt-1">
                  Food categories have not been initialized yet.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {categories.map((cat) => {
                  const isOther = cat.slug === 'other' || cat.name.toLowerCase() === 'other'
                  return (
                    <div
                      key={cat.id}
                      className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-3xl p-2 bg-emerald-50 rounded-lg">{cat.icon || '🏷️'}</span>
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                              cat.is_active !== false
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {cat.is_active !== false ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-1">{cat.name}</h3>
                        <p className="text-xs text-gray-600 leading-relaxed mb-4">
                          {cat.description ||
                            (isOther
                              ? 'Custom and assorted surplus items with donor-specified descriptions.'
                              : 'Fresh and safe food supplies ready for community distribution.')}
                        </p>
                      </div>
                      <div className="pt-3 border-t border-gray-100">
                        <button
                          onClick={() => {
                            setFilterCategory(String(cat.id))
                            setActiveTab('browse')
                          }}
                          className="w-full text-center bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold py-2 px-3 rounded-lg transition flex items-center justify-center gap-1.5"
                        >
                          <span>Browse Donations</span>
                          <span>→</span>
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* VIEW 2: DONOR DASHBOARD (MY DONATIONS & INCOMING CLAIMS) */}
        {activeTab === 'donor_dashboard' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Food Donor Dashboard</h2>
                <p className="text-sm text-gray-500">Manage your published food donations and approve NGO claim requests.</p>
              </div>
              <button
                onClick={() => setActiveTab('donor_create')}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold"
              >
                + Post New Donation
              </button>
            </div>

            {/* Incoming Claims Section */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-1">Incoming NGO Claim Requests</h3>
              <p className="text-xs text-gray-500 mb-4">Review requests submitted by verified community shelters for your donations.</p>

              {incomingRequests.length === 0 ? (
                <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                  No incoming claim requests pending review.
                </div>
              ) : (
                <div className="space-y-3">
                  {incomingRequests.map((req) => (
                    <div key={req.id} className="p-4 rounded-lg border border-gray-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-bold text-gray-900 text-sm">
                            {req.donation_title || `Donation #${req.donation}`}
                          </span>
                          {getRequestStatusBadge(req.status)}
                        </div>
                        <p className="text-xs text-gray-600 mb-0.5">
                          Requester: <strong>{req.receiver_details?.first_name ? `${req.receiver_details.first_name} ${req.receiver_details?.last_name || ''}` : 'NGO Receiver'}</strong> ({req.receiver_details?.email})
                        </p>
                        <p className="text-xs text-gray-600">
                          Requested <strong>{req.requested_servings} portions</strong>: "{req.message}"
                        </p>
                      </div>

                      {req.status === 'PENDING' && (
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleAcceptRequest(req.id)}
                            disabled={actionLoadingId === req.id}
                            className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                          >
                            {actionLoadingId === req.id ? 'Processing...' : 'Accept & Schedule Pickup'}
                          </button>
                          <button
                            onClick={() => handleRejectRequest(req.id)}
                            disabled={actionLoadingId === req.id}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                          >
                            {actionLoadingId === req.id ? '...' : 'Reject'}
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* My Donations Table */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">My Published Donations</h3>
              {myDonations.length === 0 ? (
                <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                  <p className="mb-3">You have not published any food donations yet.</p>
                  <button
                    onClick={() => setActiveTab('donor_create')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-semibold"
                  >
                    + Post Your First Donation
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 border-b text-xs text-gray-500 uppercase">
                      <tr>
                        <th className="p-3">Title</th>
                        <th className="p-3">Category</th>
                        <th className="p-3">Servings</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Expiry Deadline</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {myDonations.map((d) => (
                        <tr key={d.id} className="hover:bg-gray-50">
                          <td className="p-3 font-semibold text-gray-900">{d.title}</td>
                          <td className="p-3">
                            <span className="inline-flex items-center gap-1 font-medium text-gray-800">
                              {d.category_details?.slug === 'other' || d.category_details?.name?.toLowerCase() === 'other'
                                ? (d.other_food_item ? `📦 Other • ${d.other_food_item}` : '📦 Other')
                                : `${d.category_details?.icon ? `${d.category_details.icon} ` : ''}${d.category_details?.name || 'Cooked Meals'}`}
                            </span>
                          </td>
                          <td className="p-3">{d.servings} portions ({d.quantity} {d.unit})</td>
                          <td className="p-3">
                            {getDonationStatusBadge(d.status)}
                          </td>
                          <td className="p-3 text-xs text-gray-500">{new Date(d.expiry_at).toLocaleString()}</td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => setViewDonation(d)}
                                className="text-xs px-2 py-1 font-medium rounded text-emerald-700 hover:bg-emerald-50 transition"
                              >
                                Details
                              </button>
                              {isDonationCancellable(d.status) ? (
                                <button
                                  onClick={() => handleCancelDonation(d.id)}
                                  disabled={actionLoadingId === d.id}
                                  className="text-xs px-2.5 py-1 font-semibold rounded bg-red-50 text-red-700 hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 border border-red-200 transition"
                                  title="Cancel this donation"
                                >
                                  {actionLoadingId === d.id ? '...' : 'Cancel'}
                                </button>
                              ) : null}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 3: DONOR CREATE DONATION FORM */}
        {activeTab === 'donor_create' && (
          <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="mb-6 border-b border-gray-100 pb-4">
              <h2 className="text-2xl font-bold text-gray-900">Post Surplus Food Donation</h2>
              <p className="text-sm text-gray-500">Provide portion quantities, dietary category, and safe collection deadlines.</p>
            </div>

            <form onSubmit={handleCreateDonation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Donation Title / Item Batch</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 40 Plates Dal Tadka, Rice, and Roti"
                  value={donationForm.title}
                  onChange={(e) => setDonationForm({ ...donationForm, title: e.target.value })}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    value={donationForm.category || ''}
                    onChange={(e) => {
                      const newCatId = Number(e.target.value)
                      const selCat = categories.find((c) => c.id === newCatId)
                      const isOther = selCat?.slug === 'other' || selCat?.name.toLowerCase() === 'other'
                      setDonationForm((prev) => ({
                        ...prev,
                        category: newCatId,
                        other_food_item: isOther ? prev.other_food_item : '',
                      }))
                      setCategoryFormError('')
                      if (!isOther) setOtherFoodItemError('')
                    }}
                    className={`w-full text-sm border ${
                      categoryFormError ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-300'
                    } rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500`}
                  >
                    <option value="" disabled>-- Select Food Category --</option>
                    {categories.filter((c) => c.is_active !== false).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.icon ? `${c.icon} ` : ''}{c.name}
                      </option>
                    ))}
                  </select>
                  {categoryFormError && (
                    <p className="text-xs text-red-600 mt-1 font-medium">{categoryFormError}</p>
                  )}

                  {/* Dynamically displayed when 'Other' category is selected */}
                  {(() => {
                    const selCat = categories.find((c) => c.id === donationForm.category)
                    const isOther = selCat?.slug === 'other' || selCat?.name.toLowerCase() === 'other'
                    if (!isOther) return null
                    return (
                      <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                        <label className="block text-sm font-semibold text-gray-800 mb-1">
                          Specify Food Item <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          required
                          maxLength={100}
                          placeholder="Enter the food item..."
                          value={donationForm.other_food_item}
                          onChange={(e) => {
                            setDonationForm({ ...donationForm, other_food_item: e.target.value })
                            if (e.target.value.trim()) setOtherFoodItemError('')
                          }}
                          className={`w-full text-sm border ${
                            otherFoodItemError ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-300'
                          } bg-white rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500`}
                        />
                        <p className="text-xs text-gray-500 mt-1">Tell us what type of food you are donating.</p>
                        {otherFoodItemError && (
                          <p className="text-xs text-red-600 mt-1 font-medium">{otherFoodItemError}</p>
                        )}
                      </div>
                    )
                  })()}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dietary Type</label>
                  <select
                    value={donationForm.dietary_type}
                    onChange={(e) => setDonationForm({ ...donationForm, dietary_type: e.target.value as DietaryType })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="VEG">Vegetarian (Veg)</option>
                    <option value="NON_VEG">Non-Vegetarian</option>
                    <option value="VEGAN">Vegan</option>
                    <option value="EGG">Contains Egg</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={donationForm.quantity}
                    onChange={(e) => setDonationForm({
                      ...donationForm,
                      quantity: Number(e.target.value),
                      servings: Number(e.target.value),
                    })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                  <select
                    value={donationForm.unit}
                    onChange={(e) => setDonationForm({ ...donationForm, unit: e.target.value as QuantityUnit })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="meals">Meals / Servings</option>
                    <option value="kg">Kilograms (kg)</option>
                    <option value="packets">Packets / Boxes</option>
                    <option value="liters">Liters (L)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Shelf Life (Hours)</label>
                  <input
                    type="number"
                    min="1"
                    max="72"
                    required
                    value={donationForm.expiry_hours}
                    onChange={(e) => setDonationForm({ ...donationForm, expiry_hours: Number(e.target.value) })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City / Region</label>
                  <input
                    type="text"
                    required
                    value={donationForm.pickup_city}
                    onChange={(e) => setDonationForm({ ...donationForm, pickup_city: e.target.value })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
                  <input
                    type="tel"
                    required
                    placeholder="9876543210"
                    value={donationForm.pickup_contact_phone}
                    onChange={(e) => setDonationForm({ ...donationForm, pickup_contact_phone: e.target.value })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pickup Address / Landmark</label>
                <textarea
                  required
                  rows={2}
                  placeholder="Street address or restaurant kitchen landmark"
                  value={donationForm.pickup_address}
                  onChange={(e) => setDonationForm({ ...donationForm, pickup_address: e.target.value })}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Special Storage / Handling Instructions</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Keep refrigerated, bring thermal insulated food bags"
                  value={donationForm.special_instructions}
                  onChange={(e) => setDonationForm({ ...donationForm, special_instructions: e.target.value })}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="pt-3 flex gap-3">
                <button
                  type="submit"
                  disabled={isCreatingDonation}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
                >
                  {isCreatingDonation ? 'Publishing Food Donation...' : 'Publish Food Donation'}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('donor_dashboard')}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2.5 rounded-lg text-sm font-semibold"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* VIEW 4: NGO DASHBOARD */}
        {activeTab === 'ngo_dashboard' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">NGO Claims Hub</h2>
              <p className="text-sm text-gray-500">
                Track status of requested food donations from submission through donor acceptance and volunteer delivery.
              </p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900">My Submitted Claim Requests</h3>
                <button
                  onClick={() => setActiveTab('browse')}
                  className="text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold px-3 py-1.5 rounded-lg transition"
                >
                  + Browse Available Food
                </button>
              </div>
              {myRequests.length === 0 ? (
                <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                  <p className="mb-3">You haven't requested any food donations yet. Browse available surplus food to claim batches.</p>
                  <button
                    onClick={() => setActiveTab('browse')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow-sm"
                  >
                    Browse Available Food
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 border-b text-xs text-gray-500 uppercase">
                      <tr>
                        <th className="p-3">Donation Item</th>
                        <th className="p-3">Requested Servings</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Message</th>
                        <th className="p-3">Date</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {myRequests.map((req) => (
                        <tr key={req.id} className="hover:bg-gray-50">
                          <td className="p-3 font-semibold text-gray-900">{req.donation_title || `Donation #${req.donation}`}</td>
                          <td className="p-3">{req.requested_servings} portions</td>
                          <td className="p-3">
                            {getRequestStatusBadge(req.status)}
                          </td>
                          <td className="p-3 text-xs text-gray-600">{req.message || '—'}</td>
                          <td className="p-3 text-xs text-gray-400">{new Date(req.created_at).toLocaleDateString()}</td>
                          <td className="p-3 text-right">
                            {isRequestCancellable(req.status) ? (
                              <button
                                onClick={() => handleCancelRequest(req.id)}
                                disabled={actionLoadingId === req.id}
                                className="text-xs px-2.5 py-1 font-semibold rounded bg-red-50 text-red-700 hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 border border-red-200 transition"
                                title="Cancel this claim request"
                              >
                                {actionLoadingId === req.id ? '...' : 'Cancel'}
                              </button>
                            ) : (
                              <span className="text-xs text-gray-400">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 5: VOLUNTEER DASHBOARD */}
        {activeTab === 'volunteer_dashboard' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">Volunteer Logistics Dispatch Board</h2>
              <p className="text-sm text-gray-500">
                Claim pending food collections and perform verified milestone updates (Claim → Pick Up → Deliver → Complete).
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Available Pickups */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-gray-900 mb-1">Available for Pickup</h3>
                <p className="text-xs text-gray-500 mb-4">Accepted claims awaiting volunteer assignment.</p>

                {availablePickups.length === 0 ? (
                  <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                    No pickups currently awaiting assignment.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {availablePickups.map((p) => (
                      <div key={p.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                        <h4 className="font-bold text-gray-900 text-sm mb-1">{p.donation_details?.title || `Pickup #${p.id}`}</h4>
                        <p className="text-xs text-gray-600 mb-2">
                          <strong>Pickup Location:</strong> {p.pickup_location}
                        </p>
                        <button
                          onClick={() => handleClaimPickup(p.id)}
                          disabled={actionLoadingId === p.id}
                          className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 rounded-lg text-xs font-semibold transition"
                        >
                          {actionLoadingId === p.id ? 'Claiming Task...' : 'Claim This Delivery Task'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* My Assigned Deliveries */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-bold text-gray-900 mb-1">My Assigned Tasks</h3>
                <p className="text-xs text-gray-500 mb-4">Active deliveries assigned to you.</p>

                {myPickups.length === 0 ? (
                  <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                    You have no active deliveries assigned. Claim a task from the available board.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myPickups.map((p) => (
                      <div key={p.id} className="p-4 rounded-lg border border-gray-200 bg-white shadow-sm space-y-3">
                        <div className="flex justify-between items-start">
                          <h4 className="font-bold text-gray-900 text-sm">{p.donation_details?.title || `Pickup #${p.id}`}</h4>
                          {getPickupStatusBadge(p.status)}
                        </div>

                        <div className="text-xs text-gray-600 space-y-1">
                          <div><strong>From:</strong> {p.pickup_location}</div>
                          {p.picked_up_at && <div><strong>Picked up at:</strong> {new Date(p.picked_up_at).toLocaleTimeString()}</div>}
                          {p.delivered_at && <div><strong>Delivered at:</strong> {new Date(p.delivered_at).toLocaleTimeString()}</div>}
                        </div>

                        {/* State Transition Action Buttons */}
                        <div className="pt-2 flex gap-2">
                          {p.status === 'ASSIGNED' && (
                            <button
                              onClick={() => handleMarkPickedUp(p.id)}
                              disabled={actionLoadingId === p.id}
                              className="flex-1 bg-amber-600 hover:bg-amber-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-1.5 rounded text-xs font-semibold transition"
                            >
                              {actionLoadingId === p.id ? 'Updating...' : 'Mark Picked Up'}
                            </button>
                          )}
                          {p.status === 'PICKED_UP' && (
                            <button
                              onClick={() => handleMarkDelivered(p.id)}
                              disabled={actionLoadingId === p.id}
                              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-1.5 rounded text-xs font-semibold transition"
                            >
                              {actionLoadingId === p.id ? 'Updating...' : 'Mark Delivered'}
                            </button>
                          )}
                          {p.status === 'DELIVERED' && (
                            <button
                              onClick={() => handleMarkCompleted(p.id)}
                              disabled={actionLoadingId === p.id}
                              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-1.5 rounded text-xs font-semibold transition"
                            >
                              {actionLoadingId === p.id ? 'Completing...' : 'Verify & Complete Task'}
                            </button>
                          )}
                          {p.status === 'COMPLETED' && (
                            <div className="w-full text-center py-1 text-xs text-purple-700 font-bold bg-purple-50 rounded">
                              ✓ Completed &amp; Verified
                            </div>
                          )}
                          {p.status === 'CANCELLED' && (
                            <div className="w-full text-center py-1 text-xs text-rose-700 font-bold bg-rose-50 rounded">
                              ✕ Cancelled
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 6: ADMIN MANAGEMENT */}
        {activeTab === 'admin_dashboard' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">Platform Administrative Management</h2>
                  <p className="text-sm text-gray-500">
                    Oversee food categories, monitor real-time platform donations, and audit volunteer dispatches.
                  </p>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full uppercase">
                  Verified Admin Console
                </span>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm text-center">
                <div className="text-2xl font-extrabold text-emerald-700">
                  {impact?.metrics.total_donations ?? adminDonations.length}
                </div>
                <div className="text-xs font-semibold text-gray-500 uppercase mt-1">Total Donations</div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm text-center">
                <div className="text-2xl font-extrabold text-emerald-700">
                  {impact?.metrics.completed_donations ?? adminDonations.filter((d) => d.status === 'COMPLETED').length}
                </div>
                <div className="text-xs font-semibold text-gray-500 uppercase mt-1">Completed Deliveries</div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm text-center">
                <div className="text-2xl font-extrabold text-emerald-700">
                  {impact?.metrics.meals_rescued ?? 0}
                </div>
                <div className="text-xs font-semibold text-gray-500 uppercase mt-1">Meals Rescued</div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm text-center">
                <div className="text-2xl font-extrabold text-emerald-700">
                  {adminPickups.filter((p) => ['ASSIGNED', 'PICKED_UP', 'DELIVERED'].includes(p.status)).length}
                </div>
                <div className="text-xs font-semibold text-gray-500 uppercase mt-1">Active Pickups</div>
              </div>
            </div>

            {/* User Administration Limitation Note */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-3 shadow-sm">
              <span className="text-lg">ℹ️</span>
              <div>
                <strong className="font-semibold block mb-0.5">User Management API Notice:</strong>
                <span>
                  Direct account administration is not exposed via REST API endpoints in the current backend. User counts and volunteer participation are reported via platform-wide verified metrics.
                </span>
              </div>
            </div>

            {/* Category Management */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-1">Food Category Configuration</h3>
              <p className="text-xs text-gray-500 mb-4">Create and toggle active status for food donation classifications.</p>

              <form onSubmit={handleCreateCategory} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200 flex flex-wrap gap-3 items-end">
                <div className="w-16">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Icon</label>
                  <input
                    type="text"
                    placeholder="🏷️"
                    value={newCatIcon}
                    onChange={(e) => setNewCatIcon(e.target.value)}
                    className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500 text-center"
                  />
                </div>
                <div className="flex-1 min-w-[180px]">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Category Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dairy & Beverages"
                    value={newCatName}
                    onChange={(e) => setNewCatName(e.target.value)}
                    className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div className="flex-1 min-w-[220px]">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Description</label>
                  <input
                    type="text"
                    placeholder="Brief description of food types"
                    value={newCatDesc}
                    onChange={(e) => setNewCatDesc(e.target.value)}
                    className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <button
                  type="submit"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-semibold transition shadow-sm"
                >
                  + Add Category
                </button>
              </form>

              <div className="divide-y divide-gray-100">
                {categories.map((cat) => (
                  <div key={cat.id} className="py-3 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <span className="text-xl p-1.5 bg-emerald-50 rounded">{cat.icon || '🏷️'}</span>
                      <div>
                        <span className="font-bold text-gray-900 text-sm mr-2">{cat.name}</span>
                        <span className="text-xs text-gray-500">{cat.description || 'No description provided'}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`text-xs px-2 py-0.5 rounded font-bold ${cat.is_active !== false ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-200 text-gray-600'}`}>
                        {cat.is_active !== false ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                      <button
                        onClick={() => handleToggleCategoryActive(cat)}
                        className="text-xs text-emerald-700 hover:underline font-semibold"
                      >
                        {cat.is_active !== false ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Platform Donations Monitor */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Platform Donations Audit Log</h3>
                  <p className="text-xs text-gray-500">Real-time status monitoring and administrative cancellation.</p>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs font-semibold text-gray-600">Filter Status:</label>
                  <select
                    value={adminStatusFilter}
                    onChange={(e) => setAdminStatusFilter(e.target.value)}
                    className="text-xs border border-gray-300 rounded-lg p-1.5 focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">All Statuses ({adminDonations.length})</option>
                    <option value="AVAILABLE">Available</option>
                    <option value="REQUESTED">Requested</option>
                    <option value="ACCEPTED">Accepted</option>
                    <option value="PICKUP_ASSIGNED">Pickup Assigned</option>
                    <option value="PICKED_UP">Picked Up</option>
                    <option value="DELIVERED">Delivered</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="CANCELLED">Cancelled</option>
                    <option value="EXPIRED">Expired</option>
                  </select>
                </div>
              </div>

              {adminDonations.filter((d) => !adminStatusFilter || d.status === adminStatusFilter).length === 0 ? (
                <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                  No donations found matching the selected filter.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 border-b text-xs text-gray-500 uppercase">
                      <tr>
                        <th className="p-3">ID</th>
                        <th className="p-3">Title</th>
                        <th className="p-3">Category</th>
                        <th className="p-3">Servings</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">City</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {adminDonations
                        .filter((d) => !adminStatusFilter || d.status === adminStatusFilter)
                        .map((d) => (
                          <tr key={d.id} className="hover:bg-gray-50">
                            <td className="p-3 text-xs text-gray-400">#{d.id}</td>
                            <td className="p-3 font-semibold text-gray-900">{d.title}</td>
                            <td className="p-3 text-xs text-gray-600">
                              {d.category_details?.slug === 'other' || d.category_details?.name?.toLowerCase() === 'other'
                                ? (d.other_food_item ? `Other (${d.other_food_item})` : 'Other')
                                : d.category_details?.name || 'Cooked Food'}
                            </td>
                            <td className="p-3 text-xs">{d.servings} portions ({d.quantity} {d.unit})</td>
                            <td className="p-3">{getDonationStatusBadge(d.status)}</td>
                            <td className="p-3 text-xs text-gray-600">{d.pickup_city}</td>
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  onClick={() => setViewDonation(d)}
                                  className="text-xs px-2 py-1 font-medium rounded text-emerald-700 hover:bg-emerald-50 transition"
                                >
                                  Details
                                </button>
                                {isDonationCancellable(d.status) ? (
                                  <button
                                    onClick={() => handleCancelDonation(d.id)}
                                    disabled={actionLoadingId === d.id}
                                    className="text-xs px-2.5 py-1 font-semibold rounded bg-red-50 text-red-700 hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 border border-red-200 transition"
                                    title="Cancel this donation"
                                  >
                                    {actionLoadingId === d.id ? '...' : 'Cancel'}
                                  </button>
                                ) : null}
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Live Logistics & Pickups Dispatch Monitor */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-1">Live Volunteer Pickups &amp; Logistics Dispatch</h3>
              <p className="text-xs text-gray-500 mb-4">Monitor all delivery dispatches and volunteer execution times.</p>

              {adminPickups.length === 0 ? (
                <div className="p-8 text-center text-gray-400 bg-gray-50 rounded-lg text-sm">
                  No pickup dispatches registered on the platform yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 border-b text-xs text-gray-500 uppercase">
                      <tr>
                        <th className="p-3">Pickup ID</th>
                        <th className="p-3">Donation Title</th>
                        <th className="p-3">Volunteer</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Pickup Location</th>
                        <th className="p-3">Milestone Timestamps</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {adminPickups.map((p) => (
                        <tr key={p.id} className="hover:bg-gray-50">
                          <td className="p-3 text-xs text-gray-400 font-mono">#{p.id}</td>
                          <td className="p-3 font-semibold text-gray-900">{p.donation_details?.title || `Donation #${p.donation}`}</td>
                          <td className="p-3 text-xs text-gray-700">
                            {p.volunteer_details ? `${p.volunteer_details.first_name} (${p.volunteer_details.email})` : 'Unassigned'}
                          </td>
                          <td className="p-3">{getPickupStatusBadge(p.status)}</td>
                          <td className="p-3 text-xs text-gray-600">{p.pickup_location}</td>
                          <td className="p-3 text-xs text-gray-500">
                            {p.picked_up_at && <div>Picked up: {new Date(p.picked_up_at).toLocaleTimeString()}</div>}
                            {p.delivered_at && <div>Delivered: {new Date(p.delivered_at).toLocaleTimeString()}</div>}
                            {!p.picked_up_at && !p.delivered_at && <div>Created: {new Date(p.created_at).toLocaleTimeString()}</div>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 7: IMPACT STATS */}
        {activeTab === 'impact' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">Verified Community Rescue Metrics</h2>
              <p className="text-sm text-gray-500">
                Live platform metrics backed strictly by completed food delivery records across the FoodShare network.
              </p>
            </div>

            {/* 5 Core Impact Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              <div className="bg-white p-5 rounded-xl border border-gray-200 text-center shadow-sm">
                <div className="text-3xl font-extrabold text-emerald-600">
                  {impact?.metrics.total_donations ?? 0}
                </div>
                <div className="text-xs font-semibold text-gray-600 mt-1 uppercase">Total Donations</div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-gray-200 text-center shadow-sm">
                <div className="text-3xl font-extrabold text-emerald-600">
                  {impact?.metrics.completed_donations ?? 0}
                </div>
                <div className="text-xs font-semibold text-gray-600 mt-1 uppercase">Completed Rescues</div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-gray-200 text-center shadow-sm">
                <div className="text-3xl font-extrabold text-emerald-600">
                  {impact?.metrics.food_rescued_kg_estimate ?? 0} kg
                </div>
                <div className="text-xs font-semibold text-gray-600 mt-1 uppercase">Food Rescued</div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-gray-200 text-center shadow-sm">
                <div className="text-3xl font-extrabold text-emerald-600">
                  {impact?.metrics.meals_rescued ?? 0}
                </div>
                <div className="text-xs font-semibold text-gray-600 mt-1 uppercase">Meals Served</div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-gray-200 text-center shadow-sm col-span-2 sm:col-span-1">
                <div className="text-3xl font-extrabold text-emerald-600">
                  {impact?.metrics.completion_rate_percentage ?? 0}%
                </div>
                <div className="text-xs font-semibold text-gray-600 mt-1 uppercase">Completion Rate</div>
              </div>
            </div>

            {/* Community Network */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Active Rescue Community Network</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 flex items-center gap-3">
                  <span className="text-3xl">🍲</span>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{impact?.community.active_donors ?? 0}</div>
                    <div className="text-xs text-gray-500 font-medium uppercase">Active Food Donors</div>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 flex items-center gap-3">
                  <span className="text-3xl">🏢</span>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{impact?.community.registered_ngos ?? 0}</div>
                    <div className="text-xs text-gray-500 font-medium uppercase">Registered NGOs &amp; Shelters</div>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 flex items-center gap-3">
                  <span className="text-3xl">🚴</span>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">{impact?.community.delivery_volunteers ?? 0}</div>
                    <div className="text-xs text-gray-500 font-medium uppercase">Active Delivery Volunteers</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity Feed */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Recent Platform Activity</h3>
              {impact?.recent_activity && impact.recent_activity.length > 0 ? (
                <div className="divide-y divide-gray-100">
                  {impact.recent_activity.map((act) => (
                    <div key={act.id} className="py-3 flex justify-between items-center text-xs">
                      <div className="flex items-center gap-2">
                        <span className="p-1 rounded bg-emerald-50 text-emerald-700 font-semibold">✓</span>
                        <span className="font-semibold text-gray-800">{act.title}</span>
                        <span className="text-gray-500">— {act.donor_name} ({act.servings} portions in {act.city})</span>
                      </div>
                      <span className="text-gray-400">{new Date(act.completed_at).toLocaleTimeString()}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500 py-4 text-center">
                  Recent activities and deliveries will be logged here as community rescues occur.
                </p>
              )}
            </div>

            {/* Calculation Assumptions & Methodology */}
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900">
              <strong className="font-semibold block mb-1">Impact Calculation Methodology &amp; Assumptions:</strong>
              {impact?.assumptions ? (
                <div className="space-y-1">
                  <p>• {impact.assumptions.meals_calculation}</p>
                  <p>• {impact.assumptions.kg_calculation}</p>
                </div>
              ) : (
                <p>
                  Estimates reflect strictly completed deliveries verified by assigned volunteers. 1 standard meal is calibrated to ~0.4 kg of edible surplus rescued. Donations cancelled or expired prior to pickup are not included in rescue totals.
                </p>
              )}
            </div>
          </div>
        )}
      </main>

      {/* ── Modal: Claim Food ──────────────────────────────────────────────── */}
      {showClaimModal && selectedDonation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 mb-1">Claim Food Surplus</h3>
            <p className="text-sm text-gray-500 mb-4">{selectedDonation.title}</p>

            {claimError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
                ⚠️ {claimError}
              </div>
            )}

            <form onSubmit={handleClaimSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Required Portion Servings (Max available: {selectedDonation.servings})
                </label>
                <input
                  type="number"
                  min="1"
                  max={selectedDonation.servings}
                  value={claimServings}
                  onChange={(e) => {
                    setClaimServings(Number(e.target.value))
                    setClaimError('')
                  }}
                  className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Distribution Purpose / Beneficiary Notes</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Distribution at Hope Shelter evening meal program for 40 individuals."
                  value={claimMessage}
                  onChange={(e) => setClaimMessage(e.target.value)}
                  className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={isSubmittingClaim}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white py-2 rounded text-sm font-semibold transition"
                >
                  {isSubmittingClaim ? 'Submitting Claim...' : 'Confirm Claim Request'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowClaimModal(false)}
                  disabled={isSubmittingClaim}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded text-sm font-semibold"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Confirmation Dialog ──────────────────────────────────────── */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl animate-in fade-in duration-150">
            <h3 className="text-lg font-bold text-gray-900 mb-2">{confirmModal.title}</h3>
            <p className="text-sm text-gray-600 mb-6">{confirmModal.message}</p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmModal(null)}
                disabled={confirmModalLoading}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition"
              >
                {confirmModal.cancelText || 'Cancel'}
              </button>
              <button
                type="button"
                onClick={async () => {
                  setConfirmModalLoading(true)
                  try {
                    await confirmModal.onConfirm()
                  } finally {
                    setConfirmModalLoading(false)
                    setConfirmModal(null)
                  }
                }}
                disabled={confirmModalLoading}
                className={`px-4 py-2 text-xs font-semibold rounded-lg text-white transition disabled:bg-gray-400 ${
                  confirmModal.confirmVariant === 'danger'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-emerald-600 hover:bg-emerald-700'
                }`}
              >
                {confirmModalLoading ? 'Processing...' : (confirmModal.confirmText || 'Confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: View Donation Details ────────────────────────────────────── */}
      {viewDonation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className="text-xs font-bold px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 inline-block mb-1">
                  {viewDonation.category_details?.slug === 'other' || viewDonation.category_details?.name?.toLowerCase() === 'other'
                    ? (viewDonation.other_food_item ? `📦 Other • ${viewDonation.other_food_item}` : '📦 Other')
                    : `${viewDonation.category_details?.icon ? `${viewDonation.category_details.icon} ` : ''}${viewDonation.category_details?.name || 'Food Category'}`}
                </span>
                <h3 className="text-xl font-bold text-gray-900">{viewDonation.title}</h3>
              </div>
              <button
                onClick={() => setViewDonation(null)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm text-gray-700">
              <p className="text-xs text-gray-600 leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-100">
                {viewDonation.description || 'No additional description provided.'}
              </p>

              <div className="grid grid-cols-2 gap-3 text-xs bg-gray-50 p-3 rounded-lg border border-gray-100">
                <div>
                  <span className="text-gray-500 block">Quantity</span>
                  <span className="font-semibold text-gray-900">{viewDonation.quantity} {viewDonation.unit}</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Estimated Servings</span>
                  <span className="font-semibold text-gray-900">{viewDonation.servings} portions</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Dietary Type</span>
                  <span className="font-semibold text-gray-900">{viewDonation.dietary_type}</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Current Status</span>
                  <div className="mt-0.5">{getDonationStatusBadge(viewDonation.status)}</div>
                </div>
              </div>

              <div className="text-xs space-y-1 bg-gray-50 p-3 rounded-lg border border-gray-100">
                <div><strong>City / Region:</strong> {viewDonation.pickup_city}</div>
                <div><strong>Address:</strong> {viewDonation.pickup_address}</div>
                {viewDonation.pickup_contact_phone && (
                  <div><strong>Contact Phone:</strong> {viewDonation.pickup_contact_phone}</div>
                )}
                <div className="text-red-700 font-medium">
                  <strong>Expiry Deadline:</strong> {new Date(viewDonation.expiry_at).toLocaleString()}
                </div>
                {viewDonation.special_instructions && (
                  <div className="mt-2 text-gray-600">
                    <strong>Special Instructions:</strong> {viewDonation.special_instructions}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              {currentUser?.role === 'ngo_receiver' && viewDonation.status === 'AVAILABLE' && (
                <button
                  onClick={() => {
                    const donation = viewDonation
                    setViewDonation(null)
                    setSelectedDonation(donation)
                    setClaimServings(donation.servings)
                    setClaimError('')
                    setShowClaimModal(true)
                  }}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
                >
                  Claim Food
                </button>
              )}
              <button
                onClick={() => setViewDonation(null)}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Auth (Sign In / Register) ────────────────────────────────── */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 sm:p-8 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900 leading-tight">
                  {isRegisterMode ? 'Register for FoodShare' : 'Sign In to FoodShare'}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {isRegisterMode
                    ? 'Join as a Donor, NGO Shelter, or Volunteer to rescue food surplus.'
                    : 'Enter your credentials to access your FoodShare account.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowAuthModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={isRegisterMode ? handleRegisterSubmit : handleLoginSubmit} className="space-y-4">
              {isRegisterMode && (
                <>
                  {/* Account Role Selector */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1.5">Select Account Type *</label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setAuthRole('donor')}
                        className={`p-2.5 rounded-lg border text-left transition flex flex-col items-center text-center ${
                          authRole === 'donor'
                            ? 'border-emerald-600 bg-emerald-50 text-emerald-900 font-bold ring-1 ring-emerald-500'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <span className="text-xl mb-1">🍲</span>
                        <span className="text-xs">Food Donor</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setAuthRole('ngo_receiver')}
                        className={`p-2.5 rounded-lg border text-left transition flex flex-col items-center text-center ${
                          authRole === 'ngo_receiver'
                            ? 'border-emerald-600 bg-emerald-50 text-emerald-900 font-bold ring-1 ring-emerald-500'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <span className="text-xl mb-1">🏢</span>
                        <span className="text-xs">NGO Shelter</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setAuthRole('volunteer')}
                        className={`p-2.5 rounded-lg border text-left transition flex flex-col items-center text-center ${
                          authRole === 'volunteer'
                            ? 'border-emerald-600 bg-emerald-50 text-emerald-900 font-bold ring-1 ring-emerald-500'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <span className="text-xl mb-1">🚴</span>
                        <span className="text-xs">Volunteer</span>
                      </button>
                    </div>
                  </div>

                  {/* Name fields */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">First Name *</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Rahul"
                        value={authFirstName}
                        onChange={(e) => {
                          setAuthFirstName(e.target.value)
                          if (formErrors.first_name) setFormErrors((prev) => ({ ...prev, first_name: '' }))
                        }}
                        className={`w-full text-sm border rounded p-2 focus:ring-1 focus:ring-emerald-500 ${
                          formErrors.first_name ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                        }`}
                      />
                      {formErrors.first_name && (
                        <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                          <span>⚠</span> <span>{formErrors.first_name}</span>
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Last Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Sharma"
                        value={authLastName}
                        onChange={(e) => {
                          setAuthLastName(e.target.value)
                          if (formErrors.last_name) setFormErrors((prev) => ({ ...prev, last_name: '' }))
                        }}
                        className={`w-full text-sm border rounded p-2 focus:ring-1 focus:ring-emerald-500 ${
                          formErrors.last_name ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                        }`}
                      />
                      {formErrors.last_name && (
                        <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                          <span>⚠</span> <span>{formErrors.last_name}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Mobile Number */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Mobile Number (10 digits) *</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500 text-xs font-medium">
                        +91
                      </div>
                      <input
                        type="tel"
                        required
                        maxLength={10}
                        placeholder="9876543210"
                        value={authPhone}
                        onChange={(e) => {
                          setAuthPhone(e.target.value.replace(/\D/g, '').slice(0, 10))
                          if (formErrors.phone_number) setFormErrors((prev) => ({ ...prev, phone_number: '' }))
                        }}
                        className={`w-full text-sm pl-11 pr-3 py-2 border rounded focus:ring-1 focus:ring-emerald-500 font-mono ${
                          formErrors.phone_number ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                        }`}
                      />
                    </div>
                    {formErrors.phone_number ? (
                      <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                        <span>⚠</span> <span>{formErrors.phone_number}</span>
                      </p>
                    ) : (
                      <p className="text-[11px] text-gray-400 mt-1">Must contain exactly 10 digits without country code or special characters.</p>
                    )}
                  </div>

                  {/* Role-specific fields */}
                  {authRole === 'donor' && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Donor Category</label>
                        <select
                          value={authDonorType}
                          onChange={(e) => setAuthDonorType(e.target.value)}
                          className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500 bg-white"
                        >
                          <option value="restaurant">Restaurant / Cafe</option>
                          <option value="individual">Individual / Household</option>
                          <option value="hotel">Hotel / Banquet</option>
                          <option value="supermarket">Supermarket / Grocery</option>
                          <option value="bakery">Bakery</option>
                          <option value="caterer">Catering Service</option>
                          <option value="corporate">Corporate Cafeteria</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Kitchen / Org Name (Optional)</label>
                        <input
                          type="text"
                          placeholder="e.g. Fresh Bites Cafe"
                          value={authOrgName}
                          onChange={(e) => setAuthOrgName(e.target.value)}
                          className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500"
                        />
                      </div>
                    </div>
                  )}

                  {authRole === 'ngo_receiver' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Organization Name *</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Hope Shelter Foundation"
                        value={authOrgName}
                        onChange={(e) => {
                          setAuthOrgName(e.target.value)
                          if (formErrors.organization_name) setFormErrors((prev) => ({ ...prev, organization_name: '' }))
                        }}
                        className={`w-full text-sm border rounded p-2 focus:ring-1 focus:ring-emerald-500 ${
                          formErrors.organization_name ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                        }`}
                      />
                      {formErrors.organization_name ? (
                        <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                          <span>⚠</span> <span>{formErrors.organization_name}</span>
                        </p>
                      ) : (
                        <p className="text-[11px] text-gray-400 mt-1">Enter your registered NGO, charitable trust, or shelter name.</p>
                      )}
                    </div>
                  )}

                  {authRole === 'volunteer' && (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Vehicle / Transport Type</label>
                      <select
                        value={authVehicleType}
                        onChange={(e) => setAuthVehicleType(e.target.value)}
                        className="w-full text-sm border border-gray-300 rounded p-2 focus:ring-1 focus:ring-emerald-500 bg-white"
                      >
                        <option value="two_wheeler">Motorcycle / Scooter</option>
                        <option value="bicycle">Bicycle</option>
                        <option value="car">Car</option>
                        <option value="van">Mini-Van / Cargo Van</option>
                        <option value="walk">On Foot</option>
                      </select>
                    </div>
                  )}
                </>
              )}

              {/* Email Address */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="name@organization.org"
                  value={authEmail}
                  onChange={(e) => {
                    setAuthEmail(e.target.value)
                    if (formErrors.email) setFormErrors((prev) => ({ ...prev, email: '' }))
                  }}
                  className={`w-full text-sm border rounded p-2 focus:ring-1 focus:ring-emerald-500 ${
                    formErrors.email ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                  }`}
                />
                {formErrors.email && (
                  <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                    <span>⚠</span> <span>{formErrors.email}</span>
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-xs font-semibold text-gray-700">Password *</label>
                  {!isRegisterMode && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowAuthModal(false)
                        setForgotPasswordEmail(authEmail.trim())
                        setForgotPasswordError('')
                        setShowForgotPasswordModal(true)
                      }}
                      className="text-xs text-emerald-700 hover:text-emerald-800 hover:underline font-medium"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="••••••••"
                    value={authPassword}
                    onChange={(e) => {
                      setAuthPassword(e.target.value)
                      if (formErrors.password) setFormErrors((prev) => ({ ...prev, password: '' }))
                    }}
                    className={`w-full text-sm border rounded p-2 pr-16 focus:ring-1 focus:ring-emerald-500 ${
                      formErrors.password ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-xs font-medium text-gray-500 hover:text-gray-800"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
                {formErrors.password && (
                  <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                    <span>⚠</span> <span>{formErrors.password}</span>
                  </p>
                )}
              </div>

              {/* Register Mode extra password UI */}
              {isRegisterMode && (
                <>
                  {/* Confirm Password */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Confirm Password *</label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        placeholder="••••••••"
                        value={authConfirmPassword}
                        onChange={(e) => {
                          setAuthConfirmPassword(e.target.value)
                          if (formErrors.confirm_password) setFormErrors((prev) => ({ ...prev, confirm_password: '' }))
                        }}
                        className={`w-full text-sm border rounded p-2 pr-16 focus:ring-1 focus:ring-emerald-500 ${
                          formErrors.confirm_password || (authConfirmPassword && authPassword && authPassword !== authConfirmPassword)
                            ? 'border-rose-500 bg-rose-50/20'
                            : 'border-gray-300'
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-xs font-medium text-gray-500 hover:text-gray-800"
                      >
                        {showConfirmPassword ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    {/* Inline password mismatch directly below Confirm Password */}
                    {(formErrors.confirm_password || (authConfirmPassword && authPassword && authPassword !== authConfirmPassword)) && (
                      <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                        <span>⚠</span> <span>{formErrors.confirm_password || 'Passwords do not match.'}</span>
                      </p>
                    )}
                  </div>

                  {/* Password Strength Meter & Requirement Checklist */}
                  {authPassword && (
                    <div className="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600 font-medium">Password Strength:</span>
                        <span
                          className={`font-bold ${
                            calculatePasswordStrength(authPassword).label === 'Strong'
                              ? 'text-emerald-700'
                              : calculatePasswordStrength(authPassword).label === 'Medium'
                              ? 'text-amber-600'
                              : 'text-rose-600'
                          }`}
                        >
                          {calculatePasswordStrength(authPassword).label || 'Weak'}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${
                            calculatePasswordStrength(authPassword).color
                          } ${calculatePasswordStrength(authPassword).width}`}
                        />
                      </div>

                      <div className="pt-1.5 border-t border-gray-200/60">
                        <p className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Password requirements:</p>
                        <div className="space-y-1">
                          <div
                            className={`flex items-center space-x-1.5 ${
                              authPassword.length >= 8 ? 'text-emerald-700 font-medium' : 'text-gray-400'
                            }`}
                          >
                            <span>{authPassword.length >= 8 ? '✓' : '○'}</span>
                            <span>At least 8 characters</span>
                          </div>
                          <div
                            className={`flex items-center space-x-1.5 ${
                              authPassword && authConfirmPassword && authPassword === authConfirmPassword
                                ? 'text-emerald-700 font-medium'
                                : authConfirmPassword && authPassword !== authConfirmPassword
                                ? 'text-rose-600 font-medium'
                                : 'text-gray-400'
                            }`}
                          >
                            <span>
                              {authPassword && authConfirmPassword && authPassword === authConfirmPassword
                                ? '✓'
                                : authConfirmPassword && authPassword !== authConfirmPassword
                                ? '✗'
                                : '○'}
                            </span>
                            <span>Passwords match</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm mt-2"
              >
                {isRegisterMode ? 'Create Account' : 'Sign In'}
              </button>

              <div className="flex justify-between items-center pt-2 text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegisterMode(!isRegisterMode)
                    setAuthPassword('')
                    setAuthConfirmPassword('')
                    setFormErrors({})
                  }}
                  className="text-emerald-700 hover:underline font-semibold"
                >
                  {isRegisterMode ? 'Already have an account? Sign In' : 'Need an account? Register'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAuthModal(false)
                    setFormErrors({})
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: OTP Email Verification ───────────────────────────────────── */}
      {showOtpModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-gray-100">
            <button
              type="button"
              onClick={() => {
                setShowOtpModal(false)
                setPendingAuthSession(null)
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
              aria-label="Close modal"
            >
              ✕
            </button>

            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
                ✉
              </div>
              <h3 className="text-xl font-bold text-gray-900">Verify your email</h3>
              <p className="text-xs text-gray-500 mt-1.5 max-w-xs mx-auto">
                We sent a 6-digit verification code to:<br />
                <span className="font-semibold text-gray-800 break-all">{otpEmail}</span>
              </p>
            </div>

            {otpSuccessMessage ? (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl text-center mb-4">
                <p className="text-sm font-bold flex items-center justify-center gap-1.5">
                  <span>✓</span> <span>{otpSuccessMessage}</span>
                </p>
                <p className="text-xs text-emerald-600 mt-1">Redirecting to your dashboard...</p>
              </div>
            ) : (
              <form onSubmit={handleVerifyOtpSubmit} className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 text-center mb-3">
                    Enter 6-digit verification code
                  </label>
                  <div className="flex justify-center gap-2 sm:gap-3" onPaste={handleOtpPaste}>
                    {otpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={(el) => { otpInputRefs.current[idx] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                        className="w-11 h-12 text-center text-xl font-bold border-2 border-gray-300 rounded-lg focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200 focus:outline-none transition font-mono shadow-sm"
                        autoFocus={idx === 0}
                      />
                    ))}
                  </div>

                  {otpError && (
                    <p className="text-xs text-rose-600 mt-3 text-center flex items-center justify-center gap-1 font-medium">
                      <span>⚠</span> <span>{otpError}</span>
                    </p>
                  )}
                </div>

                <div className="text-center text-xs text-gray-500 font-medium">
                  <span>Code expires in </span>
                  <span className={otpExpirySeconds < 60 ? 'text-rose-600 font-bold' : 'text-gray-700 font-bold'}>
                    {formatTimer(otpExpirySeconds)}
                  </span>
                </div>

                {/* Local Dev Helper Callout */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-[11px] text-amber-800">
                  <div className="flex items-start gap-1.5">
                    <span className="text-sm">💡</span>
                    <div>
                      <span className="font-semibold">Local Development Mode:</span>
                      <p className="text-amber-700 mt-0.5">
                        The 6-digit code has been output to the Django backend terminal stdout (console email backend).
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <button
                    type="submit"
                    disabled={isVerifyingOtp || otpDigits.join('').length !== 6}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
                  >
                    {isVerifyingOtp ? 'Verifying...' : 'Verify Email'}
                  </button>

                  <button
                    type="button"
                    onClick={handleResendOtpSubmit}
                    disabled={isResendingOtp || resendCooldownSeconds > 0}
                    className="w-full bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed text-gray-700 py-2 rounded-lg text-xs font-semibold transition"
                  >
                    {isResendingOtp
                      ? 'Resending...'
                      : resendCooldownSeconds > 0
                      ? `Resend code in ${resendCooldownSeconds}s`
                      : 'Resend OTP'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── Modal: Login Email OTP Verification ────────────────────────── */}
      {showLoginOtpModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-gray-100">
            <button
              type="button"
              onClick={() => {
                setShowLoginOtpModal(false)
                setLoginOtpError('')
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
              aria-label="Close modal"
            >
              ✕
            </button>

            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
                🔐
              </div>
              <h3 className="text-xl font-bold text-gray-900">Two-Step Verification</h3>
              <p className="text-xs text-gray-500 mt-1.5 max-w-xs mx-auto">
                Enter the 6-digit login verification code sent to:<br />
                <span className="font-semibold text-gray-800 break-all">{loginOtpEmail}</span>
              </p>
            </div>

            {loginOtpSuccessMessage ? (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl text-center mb-4">
                <p className="text-sm font-bold flex items-center justify-center gap-1.5">
                  <span>✓</span> <span>{loginOtpSuccessMessage}</span>
                </p>
                <p className="text-xs text-emerald-600 mt-1">Redirecting to your dashboard...</p>
              </div>
            ) : (
              <form onSubmit={handleVerifyLoginOtpSubmit} className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 text-center mb-3">
                    Enter 6-digit login code
                  </label>
                  <div className="flex justify-center gap-2 sm:gap-3" onPaste={handleLoginOtpPaste}>
                    {loginOtpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={(el) => { loginOtpInputRefs.current[idx] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleLoginOtpDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleLoginOtpKeyDown(idx, e)}
                        className="w-11 h-12 text-center text-xl font-bold border-2 border-gray-300 rounded-lg focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200 focus:outline-none transition font-mono shadow-sm"
                        autoFocus={idx === 0}
                      />
                    ))}
                  </div>

                  {loginOtpError && (
                    <p className="text-xs text-rose-600 mt-3 text-center flex items-center justify-center gap-1 font-medium">
                      <span>⚠</span> <span>{loginOtpError}</span>
                    </p>
                  )}
                </div>

                <div className="text-center text-xs text-gray-500 font-medium">
                  <span>Code expires in </span>
                  <span className={loginOtpExpirySeconds < 60 ? 'text-rose-600 font-bold' : 'text-gray-700 font-bold'}>
                    {formatTimer(loginOtpExpirySeconds)}
                  </span>
                </div>

                {/* Local Dev Helper Callout */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-[11px] text-amber-800">
                  <div className="flex items-start gap-1.5">
                    <span className="text-sm">💡</span>
                    <div>
                      <span className="font-semibold">Local Development Mode:</span>
                      <p className="text-amber-700 mt-0.5">
                        The 6-digit login code has been output to the Django backend terminal stdout (console email backend).
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <button
                    type="submit"
                    disabled={isVerifyingLoginOtp || loginOtpDigits.join('').length !== 6}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
                  >
                    {isVerifyingLoginOtp ? 'Verifying...' : 'Verify Code & Sign In'}
                  </button>

                  <div className="flex justify-between items-center pt-2 text-xs">
                    <button
                      type="button"
                      disabled={isResendingLoginOtp || loginOtpCooldownSeconds > 0}
                      onClick={handleResendLoginOtpSubmit}
                      className="text-emerald-700 hover:underline font-semibold disabled:text-gray-400 disabled:no-underline disabled:cursor-not-allowed"
                    >
                      {isResendingLoginOtp
                        ? 'Sending new code...'
                        : loginOtpCooldownSeconds > 0
                        ? `Resend code in ${loginOtpCooldownSeconds}s`
                        : 'Resend Code'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowLoginOtpModal(false)
                        setShowAuthModal(true)
                        setIsRegisterMode(false)
                        setLoginOtpError('')
                      }}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ← Back to Sign In
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── Modal: Forgot Password (Step 1) ─────────────────────────────────── */}
      {showForgotPasswordModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-gray-100">
            <button
              type="button"
              onClick={() => {
                setShowForgotPasswordModal(false)
                setForgotPasswordError('')
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
              aria-label="Close modal"
            >
              ✕
            </button>

            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
                🔑
              </div>
              <h3 className="text-xl font-bold text-gray-900">Forgot Password</h3>
              <p className="text-xs text-gray-500 mt-1.5 max-w-xs mx-auto">
                Enter your registered FoodShare email address to receive a 6-digit password reset verification code.
              </p>
            </div>

            <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="name@organization.org"
                  value={forgotPasswordEmail}
                  onChange={(e) => {
                    setForgotPasswordEmail(e.target.value)
                    if (forgotPasswordError) setForgotPasswordError('')
                  }}
                  className={`w-full text-sm border rounded p-2.5 focus:ring-1 focus:ring-emerald-500 ${
                    forgotPasswordError ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                  }`}
                  autoFocus
                />
                {forgotPasswordError && (
                  <p className="text-xs text-rose-600 mt-1.5 flex items-center gap-1 font-medium">
                    <span>⚠</span> <span>{forgotPasswordError}</span>
                  </p>
                )}
              </div>

              <div className="space-y-2 pt-2">
                <button
                  type="submit"
                  disabled={forgotPasswordLoading || !forgotPasswordEmail.trim()}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
                >
                  {forgotPasswordLoading ? 'Sending Code...' : 'Send Reset Code'}
                </button>
                <div className="flex justify-between items-center pt-2 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForgotPasswordModal(false)
                      setShowAuthModal(true)
                      setIsRegisterMode(false)
                    }}
                    className="text-emerald-700 hover:underline font-semibold"
                  >
                    ← Back to Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForgotPasswordModal(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Reset Password (Step 2) ─────────────────────────────────── */}
      {showResetPasswordModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-gray-100 max-h-[90vh] overflow-y-auto">
            <button
              type="button"
              onClick={() => {
                setShowResetPasswordModal(false)
                setResetFormErrors({})
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
              aria-label="Close modal"
            >
              ✕
            </button>

            <div className="text-center mb-5">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
                🔒
              </div>
              <h3 className="text-xl font-bold text-gray-900">Set New Password</h3>
              <p className="text-xs text-gray-500 mt-1.5 max-w-xs mx-auto">
                We sent a 6-digit password reset code to:<br />
                <span className="font-semibold text-gray-800 break-all">{resetEmail}</span>
              </p>
            </div>

            {resetSuccessMessage ? (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl text-center mb-4">
                <p className="text-sm font-bold flex items-center justify-center gap-1.5">
                  <span>✓</span> <span>{resetSuccessMessage}</span>
                </p>
                <p className="text-xs text-emerald-600 mt-1">Redirecting to Sign In...</p>
              </div>
            ) : (
              <form onSubmit={handleResetPasswordSubmit} className="space-y-4">
                {/* 6-Digit OTP */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 text-center mb-2">
                    Enter 6-digit reset code *
                  </label>
                  <div className="flex justify-center gap-2 sm:gap-3" onPaste={handleResetOtpPaste}>
                    {resetOtpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={(el) => { resetOtpInputRefs.current[idx] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleResetOtpDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleResetOtpKeyDown(idx, e)}
                        className="w-11 h-12 text-center text-xl font-bold border-2 border-gray-300 rounded-lg focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200 focus:outline-none transition font-mono shadow-sm"
                        autoFocus={idx === 0}
                      />
                    ))}
                  </div>

                  {resetFormErrors.otp && (
                    <p className="text-xs text-rose-600 mt-2 text-center flex items-center justify-center gap-1 font-medium">
                      <span>⚠</span> <span>{resetFormErrors.otp}</span>
                    </p>
                  )}
                </div>

                <div className="text-center text-xs text-gray-500 font-medium">
                  <span>Code expires in </span>
                  <span className={resetExpirySeconds < 60 ? 'text-rose-600 font-bold' : 'text-gray-700 font-bold'}>
                    {formatTimer(resetExpirySeconds)}
                  </span>
                </div>

                {/* Local Dev Helper Callout */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-[11px] text-amber-800">
                  <div className="flex items-start gap-1.5">
                    <span className="text-sm">💡</span>
                    <div>
                      <span className="font-semibold">Local Development Mode:</span>
                      <p className="text-amber-700 mt-0.5">
                        The 6-digit password reset code has been output to the Django backend terminal stdout (console email backend).
                      </p>
                    </div>
                  </div>
                </div>

                {/* New Password */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">New Password *</label>
                  <div className="relative">
                    <input
                      type={showResetNewPassword ? 'text' : 'password'}
                      required
                      placeholder="••••••••"
                      value={resetNewPassword}
                      onChange={(e) => {
                        setResetNewPassword(e.target.value)
                        if (resetFormErrors.new_password) {
                          setResetFormErrors((prev) => ({ ...prev, new_password: '' }))
                        }
                      }}
                      className={`w-full text-sm border rounded p-2 pr-16 focus:ring-1 focus:ring-emerald-500 ${
                        resetFormErrors.new_password ? 'border-rose-500 bg-rose-50/20' : 'border-gray-300'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowResetNewPassword(!showResetNewPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-xs font-medium text-gray-500 hover:text-gray-800"
                    >
                      {showResetNewPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  {resetFormErrors.new_password && (
                    <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                      <span>⚠</span> <span>{resetFormErrors.new_password}</span>
                    </p>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Confirm New Password *</label>
                  <div className="relative">
                    <input
                      type={showResetConfirmPassword ? 'text' : 'password'}
                      required
                      placeholder="••••••••"
                      value={resetConfirmPassword}
                      onChange={(e) => {
                        setResetConfirmPassword(e.target.value)
                        if (resetFormErrors.confirm_password) {
                          setResetFormErrors((prev) => ({ ...prev, confirm_password: '' }))
                        }
                      }}
                      className={`w-full text-sm border rounded p-2 pr-16 focus:ring-1 focus:ring-emerald-500 ${
                        resetFormErrors.confirm_password || (resetConfirmPassword && resetNewPassword && resetNewPassword !== resetConfirmPassword)
                          ? 'border-rose-500 bg-rose-50/20'
                          : 'border-gray-300'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowResetConfirmPassword(!showResetConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-xs font-medium text-gray-500 hover:text-gray-800"
                    >
                      {showResetConfirmPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  {/* Field-level error directly under confirm password */}
                  {(resetFormErrors.confirm_password || (resetConfirmPassword && resetNewPassword && resetNewPassword !== resetConfirmPassword)) && (
                    <p className="text-xs text-rose-600 mt-1 flex items-center gap-1 font-medium">
                      <span>⚠</span> <span>{resetFormErrors.confirm_password || 'Passwords do not match.'}</span>
                    </p>
                  )}
                </div>

                {/* Password Strength & Checklist */}
                {resetNewPassword && (
                  <div className="space-y-2 pt-1 bg-gray-50 p-2.5 rounded-lg border border-gray-200">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-500 font-medium">Strength:</span>
                      <span className={`font-semibold ${
                        calculatePasswordStrength(resetNewPassword).score === 1 ? 'text-rose-600' :
                        calculatePasswordStrength(resetNewPassword).score === 2 ? 'text-amber-600' :
                        'text-emerald-600'
                      }`}>
                        {calculatePasswordStrength(resetNewPassword).label}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${calculatePasswordStrength(resetNewPassword).color} ${calculatePasswordStrength(resetNewPassword).width}`}
                      />
                    </div>
                    <div className="text-[11px] space-y-1 pt-1 text-gray-600">
                      <div className="flex items-center gap-1.5">
                        <span className={resetNewPassword.length >= 8 ? 'text-emerald-600 font-bold' : 'text-gray-400'}>
                          {resetNewPassword.length >= 8 ? '✓' : '✗'}
                        </span>
                        <span>At least 8 characters</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className={resetConfirmPassword && resetNewPassword === resetConfirmPassword ? 'text-emerald-600 font-bold' : 'text-gray-400'}>
                          {resetConfirmPassword && resetNewPassword === resetConfirmPassword ? '✓' : '✗'}
                        </span>
                        <span>Passwords match</span>
                      </div>
                    </div>
                  </div>
                )}

                {resetFormErrors.general && (
                  <p className="text-xs text-rose-600 text-center font-medium">
                    ⚠ {resetFormErrors.general}
                  </p>
                )}

                <div className="space-y-2 pt-2">
                  <button
                    type="submit"
                    disabled={
                      resetPasswordLoading ||
                      resetOtpDigits.join('').length !== 6 ||
                      !resetNewPassword ||
                      resetNewPassword.length < 8 ||
                      resetNewPassword !== resetConfirmPassword
                    }
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
                  >
                    {resetPasswordLoading ? 'Resetting Password...' : 'Reset Password'}
                  </button>

                  <button
                    type="button"
                    onClick={handleResendResetOtp}
                    disabled={isResendingResetOtp || resetCooldownSeconds > 0}
                    className="w-full bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed text-gray-700 py-2 rounded-lg text-xs font-semibold transition"
                  >
                    {isResendingResetOtp
                      ? 'Resending...'
                      : resetCooldownSeconds > 0
                      ? `Resend code in ${resetCooldownSeconds}s`
                      : 'Resend Reset Code'}
                  </button>

                  <div className="flex justify-between items-center pt-2 text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setShowResetPasswordModal(false)
                        setShowForgotPasswordModal(true)
                      }}
                      className="text-emerald-700 hover:underline font-semibold"
                    >
                      ← Change Email
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowResetPasswordModal(false)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="bg-white border-t border-gray-200 py-6 text-center text-xs text-gray-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center px-6 gap-2">
          <span>© 2026 FoodShare Platform. Community Food Donation &amp; Relief Logistics.</span>
          <span>Verified • Safe Handling • Transparent Impact</span>
        </div>
      </footer>
    </div>
  )
}

export default App
