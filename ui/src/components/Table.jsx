export function Table({ columns, data, renderFooter }) {
  return (
    <div className="ow-table" role="region" aria-live="polite">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.accessor}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty">
                No data available
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr key={row.id ?? index}>
                {columns.map((col) => (
                  <td key={col.accessor}>{col.cell ? col.cell(row) : row[col.accessor]}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
        {renderFooter && <tfoot>{renderFooter()}</tfoot>}
      </table>
    </div>
  );
}
