
interface MarketingLayoutProps {
  children: React.ReactNode;
}

const MarketingLayout = ({ children }: MarketingLayoutProps) => {

  return (
    <div className="bg-slate-100 h-full">
      <main className="pt-40 pb-20 bg-slate-100">{children}</main>
    </div>
  );
}

export default MarketingLayout;