import { ReactNode } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/empty-state'
import { LucideIcon } from 'lucide-react'

interface DataTableProps<T> {
  data?: T[]
  columns: {
    key: keyof T | 'actions'
    label: string
    render?: (item: T, value: T[keyof T] | null) => ReactNode
  }[]
  loading?: boolean
  emptyState?: {
    icon: LucideIcon
    title: string
    description: string
    action?: ReactNode
  }
}

export function DataTable<T>({ 
  data, 
  columns, 
  loading = false,
  emptyState
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column, index) => (
                <TableHead key={index}>{column.label}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                {columns.map((_, colIndex) => (
                  <TableCell key={colIndex}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    )
  }

  if (!data?.length && emptyState) {
    return (
      <EmptyState
        icon={emptyState.icon}
        title={emptyState.title}
        description={emptyState.description}
        action={emptyState.action}
      />
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column, index) => (
              <TableHead key={index}>{column.label}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((item, index) => (
            <TableRow key={index}>
              {columns.map((column, colIndex) => (
                <TableCell key={colIndex}>
                  {column.render
                    ? column.render(item, column.key === 'actions' ? null : item[column.key])
                    : column.key === 'actions' 
                    ? null 
                    : String(item[column.key] ?? '')}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
