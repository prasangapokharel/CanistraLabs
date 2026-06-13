import { redirect } from 'next/navigation';

export default function EditProjectRedirect({ params }: { params: { id: string } }) {
  redirect(`/dashboard/projects/${params.id}`);
}
