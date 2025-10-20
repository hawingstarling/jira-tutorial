import Navbar from "./_components/navbar";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout = ({ children }: DashboardLayoutProps) => {

  return (
    <div className="h-full">
      <Navbar />
      {children}
    </div>
  );
}

export default DashboardLayout;