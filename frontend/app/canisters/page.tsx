import { redirect } from 'next/navigation';

export default function CanistersRootRedirect() {
  redirect('/dashboard/projects');
}
