import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-24 text-center">
      <h1 className="font-serif text-3xl">Nothing on this part of the wall.</h1>
      <Link href="/" className="btn btn-primary mt-6">Back to the Wall</Link>
    </div>
  );
}
