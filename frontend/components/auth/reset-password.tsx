"use client"

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSearchParams, useRouter } from 'next/navigation'
import { Lock, Loader2, AlertCircle, CheckCircle2, Eye, EyeOff } from 'lucide-react'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Alert, AlertDescription } from '@/components/ui/alert'

import { useResetPassword, useVerifyResetToken } from '@/hooks/api/useAuth'

const resetPasswordSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must be less than 100 characters'),
  confirmPassword: z
    .string()
    .min(8, 'Password must be at least 8 characters'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>

export function ResetPasswordForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')

  const resetPasswordMutation = useResetPassword()
  const verifyTokenQuery = useVerifyResetToken(token)

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  })

  // Redirect if no token provided
  useEffect(() => {
    if (!token) {
      router.push('/auth/forgot-password')
    }
  }, [token, router])

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) return

    try {
      await resetPasswordMutation.mutateAsync({
        token,
        password: data.password,
      })
      setIsSubmitted(true)
    } catch {
      // Error handling is done by the hook
    }
  }

  const isLoading = resetPasswordMutation.isPending || verifyTokenQuery.isLoading
  const hasError = resetPasswordMutation.isError || verifyTokenQuery.isError
  const tokenError = verifyTokenQuery.isError

  // Show loading state while verifying token
  if (verifyTokenQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm text-muted-foreground">Verifying reset token...</span>
        </div>
      </div>
    )
  }

  // Show error if token is invalid
  if (tokenError) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Invalid or expired reset link</strong><br />
            This password reset link is invalid or has expired. Please request a new one.
          </AlertDescription>
        </Alert>

        <Button
          type="button"
          variant="outline"
          onClick={() => router.push('/auth/forgot-password')}
          className="w-full"
        >
          Request new reset link
        </Button>
      </div>
    )
  }

  // Show success message after password reset
  if (isSubmitted && resetPasswordMutation.isSuccess) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            <strong>Password reset successful!</strong><br />
            Your password has been changed. You can now sign in with your new password.
          </AlertDescription>
        </Alert>

        <Button
          type="button"
          onClick={() => router.push('/auth/login')}
          className="w-full"
        >
          Continue to sign in
        </Button>
      </div>
    )
  }

  if (!token) {
    return null // Will redirect
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* General Error Alert */}
        {hasError && !tokenError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {resetPasswordMutation.error?.message || 'Failed to reset password. Please try again.'}
            </AlertDescription>
          </Alert>
        )}

        {/* New Password Field */}
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>New Password</FormLabel>
              <FormControl>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your new password"
                    disabled={isLoading}
                    autoComplete="new-password"
                    {...field}
                  />
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full w-10 px-3 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading}
                    tabIndex={-1}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="sr-only">
                      {showPassword ? 'Hide password' : 'Show password'}
                    </span>
                  </Button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Confirm Password Field */}
        <FormField
          control={form.control}
          name="confirmPassword"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm New Password</FormLabel>
              <FormControl>
                <div className="relative">
                  <Input
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your new password"
                    disabled={isLoading}
                    autoComplete="new-password"
                    {...field}
                  />
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full w-10 px-3 hover:bg-transparent"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    disabled={isLoading}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="sr-only">
                      {showConfirmPassword ? 'Hide password' : 'Show password'}
                    </span>
                  </Button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Password Requirements */}
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">Password requirements:</p>
          <ul className="text-xs text-muted-foreground space-y-1">
            <li>• At least 8 characters long</li>
            <li>• Mix of uppercase and lowercase letters recommended</li>
            <li>• Include numbers and special characters for better security</li>
          </ul>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isLoading ? 'Updating password...' : 'Update password'}
        </Button>

        {/* Security Notice */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            Your new password will take effect immediately. You&apos;ll need to sign in with your new password.
          </p>
        </div>
      </form>
    </Form>
  )
}
